# ===== register_pc.py (매장 PC 등록 스크립트) =====
"""
매장 PC 등록 스크립트
PC 고유번호를 수집하여 서비스에 등록 요청
승인 후 토큰을 저장하여 자동 인증
"""

import requests
import sys
import os
import json

# pc_identifier 모듈 import
try:
    from pc_identifier import get_pc_info
except ImportError:
    print("❌ 오류: pc_identifier.py 파일을 찾을 수 없습니다.")
    print("   register_pc.py와 같은 디렉토리에 pc_identifier.py가 있어야 합니다.")
    sys.exit(1)

# 토큰 저장 파일 경로
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "pc_token.json")

def load_pc_token():
    """저장된 PC 토큰 로드"""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("pc_token"), data.get("server_url")
        except Exception:
            pass
    return None, None

def save_pc_token(pc_token, server_url):
    """PC 토큰 저장"""
    try:
        data = {
            "pc_token": pc_token,
            "server_url": server_url
        }
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"토큰 저장 실패: {e}")
        return False

def check_pc_status(server_url, pc_unique_id):
    """PC 등록 상태 확인"""
    try:
        response = requests.post(
            f"{server_url}/api/check_pc_status",
            json={"pc_unique_id": pc_unique_id},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"상태 확인 실패: {e}")
        return None

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
                pc_code = data.get("pc_code", pc_info['unique_id'][:8].upper())
                print(f"✅ PC 등록 성공!")
                print(f"   매장: {store_name}")
                print(f"   타석: {bay_name}")
                print(f"   PC 이름: {pc_name}")
                print(f"   PC 코드: {pc_code}")
                print()
                print("=" * 60)
                print("⚠️ 중요: 슈퍼 관리자의 승인을 기다려야 합니다.")
                print("   승인 후 샷 수집 프로그램을 실행할 수 있습니다.")
                print("=" * 60)
                return True
            else:
                print(f"❌ 등록 실패: {data.get('error', '알 수 없는 오류')}")
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
    
    # 저장된 토큰 확인
    saved_token, saved_url = load_pc_token()
    if saved_token:
        print("⚠️ 이미 등록된 PC가 감지되었습니다.")
        print(f"   토큰: {saved_token[:20]}...")
        print()
        choice = input("재등록하시겠습니까? (y/N): ").strip().lower()
        if choice != 'y' and choice != 'yes':
            print("등록이 취소되었습니다.")
            return 0
    
    # PC 정보 수집
    print("PC 정보 수집 중...")
    try:
        pc_info = get_pc_info()
    except Exception as e:
        print(f"❌ PC 정보 수집 실패: {e}")
        return 1
    
    # 필수 정보 확인
    mac_address = pc_info.get("mac_address")
    pc_uuid = pc_info.get("system_uuid") or pc_info.get("machine_guid")
    
    if not mac_address:
        print("❌ MAC Address를 수집할 수 없습니다.")
        return 1
    
    if not pc_uuid:
        print("❌ PC UUID를 수집할 수 없습니다.")
        return 1
    
    print(f"✅ PC 고유번호: {pc_info['unique_id']}")
    print(f"   MAC 주소: {mac_address}")
    print(f"   PC UUID: {pc_uuid}")
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
        print()
        print("💡 다음 단계:")
        print("   1. 슈퍼 관리자에게 승인 요청")
        print("   2. 승인 후 이 프로그램을 다시 실행하면 자동으로 토큰이 저장됩니다")
        print("   3. 샷 수집 프로그램(main.py)이 자동으로 인증됩니다")
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
