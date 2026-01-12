# ===== register_pc.py (매장 PC 등록 스크립트) =====
"""
매장 PC 등록 스크립트
PC 고유번호를 수집하여 서비스에 등록 요청
"""

import requests
import sys
import os

# pc_identifier 모듈 import
try:
    from pc_identifier import get_pc_info
except ImportError:
    print("❌ 오류: pc_identifier.py 파일을 찾을 수 없습니다.")
    print("   register_pc.py와 같은 디렉토리에 pc_identifier.py가 있어야 합니다.")
    sys.exit(1)

def register_pc_to_server(server_url, store_name, bay_name, pc_name, pc_info):
    """서버에 PC 등록 요청"""
    try:
        payload = {
            "store_name": store_name,
            "bay_name": bay_name,
            "pc_name": pc_name,
            "pc_info": pc_info
        }
        
        response = requests.post(
            f"{server_url}/api/register_pc",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ PC 등록 성공!")
                print(f"   매장: {store_name}")
                print(f"   타석: {bay_name}")
                print(f"   PC 이름: {pc_name}")
                print(f"   PC 고유번호: {pc_info['unique_id']}")
                print()
                print("=" * 60)
                print("⚠️ 중요: 슈퍼 관리자의 승인을 기다려야 합니다.")
                print("   승인 후 샷 수집 프로그램을 실행할 수 있습니다.")
                print("=" * 60)
                return True
            else:
                print(f"❌ 등록 실패: {data.get('error', data.get('message', '알 수 없는 오류'))}")
                return False
        else:
            print(f"❌ 서버 오류: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   오류: {error_data.get('error', response.text)}")
            except:
                print(f"   응답: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 서버 연결 실패: {server_url}")
        print("   서버 URL이 올바른지 확인해주세요.")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 서버 응답 시간 초과")
        return False
    except Exception as e:
        print(f"❌ 등록 요청 실패: {e}")
        return False

def main():
    print("=" * 60)
    print("매장 PC 등록 프로그램")
    print("=" * 60)
    print()
    
    # PC 정보 수집
    print("PC 정보 수집 중...")
    try:
        pc_info = get_pc_info()
    except Exception as e:
        print(f"❌ PC 정보 수집 실패: {e}")
        return 1
    
    print(f"✅ PC 고유번호: {pc_info['unique_id']}")
    print(f"   호스트명: {pc_info['hostname']}")
    print(f"   플랫폼: {pc_info['platform']}")
    print()
    
    # 사용자 입력
    print("등록 정보를 입력하세요:")
    print("(이 정보는 슈퍼 관리자가 PC를 구분하는 데 사용됩니다)")
    print()
    
    store_name = input("매장명: ").strip()
    if not store_name:
        print("❌ 매장명을 입력해야 합니다.")
        return 1
    
    bay_name = input("타석번호/룸번호 (예: 1번, A타석, 101호): ").strip()
    if not bay_name:
        print("❌ 타석번호를 입력해야 합니다.")
        return 1
    
    pc_name = input("PC 이름 (예: 타석1-PC, 룸A-PC): ").strip()
    if not pc_name:
        print("❌ PC 이름을 입력해야 합니다.")
        return 1
    
    print()
    print("입력한 정보 확인:")
    print(f"  매장명: {store_name}")
    print(f"  타석번호: {bay_name}")
    print(f"  PC 이름: {pc_name}")
    print()
    confirm = input("위 정보가 맞습니까? (Y/n): ").strip().lower()
    if confirm and confirm != 'y' and confirm != 'yes':
        print("등록이 취소되었습니다.")
        return 1
    
    # 서버 URL 입력
    print()
    print("서버 URL을 입력하세요:")
    print("(예: https://golf-api-production.up.railway.app)")
    print("(환경 변수 SERVER_URL이 설정되어 있으면 기본값으로 사용)")
    default_url = os.environ.get("SERVER_URL", "")
    if default_url:
        print(f"(기본값: {default_url})")
    server_url = input("서버 URL (엔터 시 기본값): ").strip()
    if not server_url:
        if default_url:
            server_url = default_url
        else:
            print("❌ 서버 URL을 입력해야 합니다.")
            return 1
    
    # URL 정규화 (끝의 / 제거)
    server_url = server_url.rstrip('/')
    
    # 등록 요청
    print()
    print("=" * 60)
    print(f"서버에 등록 요청 중: {server_url}")
    print("=" * 60)
    print()
    success = register_pc_to_server(server_url, store_name, bay_name, pc_name, pc_info)
    
    if success:
        print()
        print("=" * 60)
        print("등록 완료!")
        print("=" * 60)
        return 0
    else:
        print()
        print("=" * 60)
        print("등록 실패. 다시 시도해주세요.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
