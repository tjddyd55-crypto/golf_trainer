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
    print("[ERROR] 오류: pc_identifier.py 파일을 찾을 수 없습니다.")
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

def register_pc_to_server(server_url, registration_key, store_name, bay_name, pc_name, pc_info):
    """서버에 PC 등록 요청 (등록 키 포함)"""
    try:
        payload = {
            "registration_key": registration_key,
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
                pc_token = data.get("pc_token")
                print(f"[OK] PC 등록 성공!")
                print(f"   매장: {store_name}")
                print(f"   타석: {bay_name}")
                print(f"   PC 이름: {pc_name}")
                if pc_token:
                    print(f"   PC 토큰: {pc_token[:20]}...")
                    # 토큰 저장
                    save_pc_token(pc_token, server_url)
                    print()
                    print("=" * 60)
                    print("[OK] PC 등록이 완료되었습니다.")
                    print("   토큰이 자동으로 저장되었습니다.")
                    print("   샷 수집 프로그램을 실행할 수 있습니다.")
                    print("=" * 60)
                return True
            else:
                print(f"[ERROR] 등록 실패: {data.get('error', '알 수 없는 오류')}")
                return False
        else:
            print(f"[ERROR] 서버 오류: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   오류: {error_data.get('error', response.text)}")
            except:
                print(f"   응답: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] 서버 연결 실패: {server_url}")
        print("   서버 URL이 올바른지 확인해주세요.")
        return False
    except requests.exceptions.Timeout:
        print(f"[ERROR] 서버 응답 시간 초과")
        return False
    except Exception as e:
        print(f"[ERROR] 등록 요청 실패: {e}")
        return False

def main():
    print("=" * 60)
    print("매장 PC 등록 프로그램")
    print("=" * 60)
    print()
    
    # 저장된 토큰 확인 (토큰이 있으면 등록 코드 입력 불필요)
    saved_token, saved_url = load_pc_token()
    if saved_token:
        print("[OK] 이미 등록된 PC입니다.")
        print(f"   토큰: {saved_token[:20]}...")
        print()
        print("이 PC는 이미 등록되어 있습니다.")
        print("샷 수집 프로그램을 실행할 수 있습니다.")
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
        print(f"[ERROR] PC 정보 수집 실패: {e}")
        return 1
    
    # 필수 정보 확인
    mac_address = pc_info.get("mac_address")
    pc_uuid = pc_info.get("system_uuid") or pc_info.get("machine_guid")
    
    if not mac_address:
        print("[ERROR] MAC Address를 수집할 수 없습니다.")
        return 1
    
    if not pc_uuid:
        print("[ERROR] PC UUID를 수집할 수 없습니다.")
        return 1
    
    print(f"[OK] PC 고유번호: {pc_info['unique_id']}")
    print(f"     MAC 주소: {mac_address}")
    print(f"     PC UUID: {pc_uuid}")
    print(f"     호스트명: {pc_info['hostname']}")
    print(f"     플랫폼: {pc_info['platform']}")
    print()
    
    # 사용자 입력 (등록 키, 매장명, 룸/타석)
    print("등록 정보를 입력하세요:")
    print()
    
    registration_key = input("PC 등록 코드: ").strip().upper()
    if not registration_key:
        print("[ERROR] PC 등록 코드를 입력해야 합니다.")
        return 1
    
    store_name = input("매장명: ").strip()
    if not store_name:
        print("[ERROR] 매장명을 입력해야 합니다.")
        return 1
    
    bay_name = input("룸 또는 타석: ").strip()
    if not bay_name:
        print("[ERROR] 룸 또는 타석을 입력해야 합니다.")
        return 1
    
    # PC 이름 자동 생성 (매장명 + 룸번호 + "-PC")
    pc_name = f"{store_name}-{bay_name}-PC"
    
    print()
    print("입력한 정보 확인:")
    print(f"  PC 등록 코드: {registration_key}")
    print(f"  매장명: {store_name}")
    print(f"  룸 또는 타석: {bay_name}")
    print()
    confirm = input("위 정보가 맞습니까? (Y/n): ").strip().lower()
    if confirm and confirm != 'y' and confirm != 'yes':
        print("등록이 취소되었습니다.")
        return 1
    
    # 서버 URL 가져오기 (환경 변수 또는 기본값)
    # 환경 변수가 없으면 Railway 기본 URL 사용 (운영 시 환경 변수로 오버라이드)
    server_url = os.environ.get("SERVER_URL", "https://golf-api-production-e675.up.railway.app")
    
    # URL 정규화 (끝의 / 제거)
    server_url = server_url.rstrip('/')
    
    # 등록 요청
    print()
    print("=" * 60)
    print(f"서버에 등록 요청 중: {server_url}")
    print("=" * 60)
    print()
    success = register_pc_to_server(server_url, registration_key, store_name, bay_name, pc_name, pc_info)
    
    if success:
        print()
        print("=" * 60)
        print("등록 완료!")
        print("=" * 60)
        print()
        print("[INFO] 다음 단계:")
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
