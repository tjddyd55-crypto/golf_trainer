# ===== 등록 코드 생성 (공개 URL 사용) =====
"""
Railway PostgreSQL 공개 연결 정보를 사용하여 등록 코드를 생성합니다.

사용법:
1. Railway > PostgreSQL 서비스 > Connect 탭에서 공개 연결 정보 확인
2. 또는 golf-api 서비스 > Variables에서 공개 DATABASE_URL 확인
3. 아래 DATABASE_URL을 수정하고 실행
"""
import os
import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("[오류] psycopg2가 설치되지 않았습니다.")
    sys.exit(1)

# Railway PostgreSQL 공개 연결 URL (아래를 수정하세요)
# 형식: postgresql://user:password@host:port/database
# Railway > PostgreSQL > Connect 탭에서 확인 가능
DATABASE_URL = os.environ.get("DATABASE_URL_PUBLIC") or input("DATABASE_URL (공개 주소) 입력: ").strip()

if not DATABASE_URL:
    print("\n[오류] DATABASE_URL이 필요합니다.")
    print("\nRailway에서 공개 연결 정보 확인:")
    print("1. Railway > PostgreSQL 서비스 > Connect 탭")
    print("2. 또는 golf-api 서비스 > Variables > DATABASE_URL (공개 주소)")
    sys.exit(1)

def main():
    print("=" * 50)
    print("GOLF-TEST 등록 코드 생성")
    print("=" * 50)
    
    try:
        print("\n데이터베이스 연결 중...")
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
            return True
        else:
            print("\n[경고] 코드 생성 실패")
            return False
        
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"\n[오류] 데이터베이스 연결 실패: {e}")
        print("\n확인사항:")
        print("1. DATABASE_URL이 공개 주소인지 확인 (railway.internal이 아닌)")
        print("2. Railway > PostgreSQL > Connect 탭에서 공개 연결 정보 확인")
        return False
    except Exception as e:
        print(f"\n[오류] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
