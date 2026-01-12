# ===== 등록 코드 즉시 생성 스크립트 =====
import os
import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("[오류] psycopg2가 설치되지 않았습니다.")
    print("설치: pip install psycopg2-binary")
    sys.exit(1)

# Railway 내부 주소 (외부 접근 불가능할 수 있음)
# 공개 URL이 필요할 수 있습니다
DATABASE_URL = "postgresql://postgres:iYYgdGvmTCsNAufPMOzGNDBIswuMkcjn@postgres.railway.internal:5432/railway"

def main():
    print("=" * 50)
    print("GOLF-TEST 등록 코드 생성")
    print("=" * 50)
    
    try:
        print("\n데이터베이스 연결 시도 중...")
        print("(내부 주소이므로 연결이 실패할 수 있습니다)")
        
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("[성공] 데이터베이스 연결 성공!")
        
        print("\n기존 ACTIVE 코드 폐기 중...")
        cur.execute("""
            UPDATE pc_registration_codes 
            SET status = 'REVOKED', revoked_at = CURRENT_TIMESTAMP
            WHERE status = 'ACTIVE'
        """)
        print(f"  -> {cur.rowcount}개 코드 폐기됨")
        
        print("\nGOLF-TEST 코드 생성 중...")
        cur.execute("""
            INSERT INTO pc_registration_codes (
                code, status, issued_by, notes, created_at
            ) VALUES (
                'GOLF-TEST', 'ACTIVE', 'test_script', '테스트용 등록 코드', CURRENT_TIMESTAMP
            )
            ON CONFLICT (code) DO UPDATE SET
                status = 'ACTIVE',
                revoked_at = NULL,
                issued_by = 'test_script',
                notes = '테스트용 등록 코드',
                created_at = CURRENT_TIMESTAMP
        """)
        
        conn.commit()
        
        cur.execute("""
            SELECT code, status, issued_by, created_at 
            FROM pc_registration_codes 
            WHERE code = 'GOLF-TEST'
        """)
        result = cur.fetchone()
        
        if result:
            print(f"\n[성공] 등록 코드 생성 완료!")
            print(f"\n등록 코드: {result['code']}")
            print(f"상태: {result['status']}")
            print(f"\n이제 register_pc.exe에서 'GOLF-TEST'를 사용하세요.")
        else:
            print("\n[경고] 코드 생성 실패")
        
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"\n[오류] 데이터베이스 연결 실패: {e}")
        print("\nRailway 내부 주소는 외부에서 접근할 수 없습니다.")
        print("\n대안:")
        print("1. Railway PostgreSQL 서비스의 공개 연결 정보 확인")
        print("2. 또는 Railway CLI 사용: railway run python create_code_now.py")
        print("3. 또는 Railway 대시보드에서 직접 SQL 실행")
    except Exception as e:
        print(f"\n[오류] 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
