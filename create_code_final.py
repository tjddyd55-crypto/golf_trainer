# ===== 등록 코드 생성 (공개 URL 사용) =====
import psycopg2
from psycopg2.extras import RealDictCursor

# Railway PostgreSQL 공개 연결 URL
DATABASE_URL = "postgresql://postgres:iYYgdGvmTCsNAufPMOzGNDBIswuMkcjn@crossover.proxy.rlwy.net:26154/railway"

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
        print(f"발급자: {result['issued_by']}")
        print(f"생성일: {result['created_at']}")
        print(f"\n이제 register_pc.exe에서 'GOLF-TEST'를 사용하세요.")
    else:
        print("\n[경고] 코드 생성 실패")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n[오류] 오류 발생: {e}")
    import traceback
    traceback.print_exc()
