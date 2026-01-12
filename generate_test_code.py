# ===== 등록 코드 생성 스크립트 (테스트용) =====
"""
매장 PC 등록 테스트용 등록 코드 생성 스크립트
Railway API를 통해 등록 코드를 생성합니다.

사용법:
1. Railway에 배포된 API 사용 (권장):
   python generate_test_code.py

2. 또는 SQL 스크립트 직접 실행:
   Railway PostgreSQL에서 create_test_registration_code.sql 실행
"""
import requests
import os

# Railway API URL (환경 변수 또는 기본값)
API_URL = os.environ.get("API_URL", "https://golf-api-production-e675.up.railway.app")
SUPER_ADMIN_USERNAME = os.environ.get("SUPER_ADMIN_USERNAME", "admin")
SUPER_ADMIN_PASSWORD = os.environ.get("SUPER_ADMIN_PASSWORD", "endolpin0!")

def main():
    print("=" * 50)
    print("PC 등록 코드 생성 (테스트용)")
    print("=" * 50)
    print(f"\nAPI URL: {API_URL}")
    print(f"관리자: {SUPER_ADMIN_USERNAME}")
    print("\n등록 코드 생성 중...")
    
    try:
        # golf-api 호출
        response = requests.post(
            f"{API_URL}/api/admin/pc-registration-codes",
            json={
                "username": SUPER_ADMIN_USERNAME,
                "password": SUPER_ADMIN_PASSWORD,
                "notes": "테스트용 등록 코드"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                code = data.get("registration_code") or data.get("registration_key")
                print(f"\n[성공] 등록 코드 생성 완료!")
                print(f"\n등록 코드: {code}")
                print(f"\n이 코드를 register_pc.exe에서 사용하세요.")
                print("=" * 50)
            else:
                print(f"\n[실패] 등록 코드 생성 실패: {data.get('error') or data.get('message')}")
        elif response.status_code == 404:
            print(f"\n[경고] API 엔드포인트를 찾을 수 없습니다.")
            print(f"아직 Railway에 배포되지 않았을 수 있습니다.")
            print(f"\n대안: Railway PostgreSQL에서 직접 SQL 실행")
            print(f"파일: create_test_registration_code.sql")
            print(f"\n또는 임시 테스트 코드 사용: GOLF-TEST")
        else:
            print(f"\n[실패] API 호출 실패: {response.status_code}")
            print(f"응답: {response.text[:200]}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n[오류] 네트워크 오류: {e}")
        print("\n팁:")
        print("1. API_URL 환경 변수를 확인하세요.")
        print("2. Railway 서비스가 실행 중인지 확인하세요.")
        print("3. SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD를 확인하세요.")
        print("\n대안: Railway PostgreSQL에서 create_test_registration_code.sql 실행")
    except Exception as e:
        print(f"\n[오류] 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
