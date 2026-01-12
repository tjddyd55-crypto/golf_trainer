# ===== 테스트용 등록 코드 직접 삽입 스크립트 =====
"""
Railway PostgreSQL에 직접 연결하여 테스트용 등록 코드를 생성합니다.
DATABASE_URL 환경 변수가 필요합니다.
"""
import os
import sys

# 공유 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from shared import database
except ImportError as e:
    print(f"[오류] shared 모듈을 찾을 수 없습니다: {e}")
    print("현재 디렉토리에서 실행하세요.")
    sys.exit(1)

def main():
    print("=" * 50)
    print("테스트용 등록 코드 생성")
    print("=" * 50)
    
    # DATABASE_URL 확인
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("\n[오류] DATABASE_URL 환경 변수가 설정되지 않았습니다.")
        print("\nRailway에서 DATABASE_URL을 복사하여 설정하세요:")
        print("1. Railway 대시보드 > PostgreSQL 서비스 > Variables")
        print("2. DATABASE_URL 복사")
        print("3. PowerShell에서 실행:")
        print("   $env:DATABASE_URL='postgresql://...'")
        print("   python insert_test_code.py")
        return
    
    print(f"\n데이터베이스 연결 중...")
    
    try:
        conn = database.get_db_connection()
        cur = conn.cursor()
        
        # 기존 ACTIVE 코드를 REVOKED로 변경
        print("기존 ACTIVE 코드를 REVOKED로 변경 중...")
        cur.execute("""
            UPDATE pc_registration_codes 
            SET status = 'REVOKED', 
                revoked_at = CURRENT_TIMESTAMP
            WHERE status = 'ACTIVE'
        """)
        revoked_count = cur.rowcount
        print(f"  -> {revoked_count}개 코드 폐기됨")
        
        # GOLF-TEST 코드 생성 또는 업데이트
        print("\nGOLF-TEST 코드 생성 중...")
        cur.execute("""
            INSERT INTO pc_registration_codes (
                code, 
                status, 
                issued_by, 
                notes,
                created_at
            ) VALUES (
                'GOLF-TEST',
                'ACTIVE',
                'test_script',
                '테스트용 등록 코드',
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (code) DO UPDATE SET
                status = 'ACTIVE',
                revoked_at = NULL,
                issued_by = 'test_script',
                notes = '테스트용 등록 코드',
                created_at = CURRENT_TIMESTAMP
        """)
        
        conn.commit()
        
        # 생성된 코드 확인
        cur.execute("""
            SELECT code, status, issued_by, created_at 
            FROM pc_registration_codes 
            WHERE code = 'GOLF-TEST'
        """)
        result = cur.fetchone()
        
        if result:
            print(f"\n[성공] 등록 코드 생성 완료!")
            print(f"\n등록 코드: {result[0]}")
            print(f"상태: {result[1]}")
            print(f"발급자: {result[2]}")
            print(f"생성일: {result[3]}")
            print(f"\n이제 register_pc.exe에서 'GOLF-TEST'를 사용하세요.")
        else:
            print("\n[경고] 코드가 생성되었지만 조회에 실패했습니다.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n[오류] 데이터베이스 오류: {e}")
        import traceback
        traceback.print_exc()
        print("\n팁:")
        print("1. DATABASE_URL이 올바른지 확인하세요.")
        print("2. Railway PostgreSQL 서비스가 실행 중인지 확인하세요.")
        print("3. 네트워크 연결을 확인하세요.")

if __name__ == "__main__":
    main()
