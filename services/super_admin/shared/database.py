# ===== shared/database.py (공유 데이터베이스 모듈) =====
import os
import psycopg2
from psycopg2 import errors as psycopg2_errors
from psycopg2.extras import RealDictCursor
from datetime import datetime
from urllib.parse import urlparse
import random
import string
import secrets
import hashlib

# PostgreSQL 연결 정보 (Railway 환경 변수 필수)
# 🔒 보안: 프로덕션에서는 DATABASE_URL 환경 변수가 반드시 설정되어야 함
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("[ERROR] DATABASE_URL 환경 변수가 설정되지 않았습니다.", flush=True)
    print("[ERROR] Railway 환경 변수에서 DATABASE_URL을 설정하세요.", flush=True)
    # 개발 환경에서만 기본값 사용 (프로덕션에서는 에러 발생)
    if os.environ.get("RAILWAY_ENVIRONMENT") == "production":
        raise ValueError("DATABASE_URL environment variable is required in production")
    DATABASE_URL = "postgresql://user:password@localhost:5432/golf_data"
    print("[WARNING] 개발 환경 기본값 사용 중 (프로덕션에서는 사용 금지)", flush=True)

def get_db_connection():
    """PostgreSQL 데이터베이스 연결"""
    try:
        # 🔒 보안: DATABASE_URL에 민감한 정보가 포함되어 있으므로 로그에 출력하지 않음
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
        return conn
    except psycopg2.OperationalError as e:
        # 🔒 보안: 연결 오류 메시지에서 DATABASE_URL의 민감한 정보 제거
        # psycopg2 오류 메시지에는 일반적으로 DB URL이 포함되지 않지만, 안전을 위해 처리
        error_msg = str(e)
        # DATABASE_URL의 민감한 부분을 오류 메시지에서 제거
        if DATABASE_URL:
            # 호스트:포트 부분 제거
            if '@' in DATABASE_URL:
                host_part = DATABASE_URL.split('@')[-1]
                error_msg = error_msg.replace(host_part, '[REDACTED]')
            # 사용자명:비밀번호 부분 제거
            if '://' in DATABASE_URL and '@' in DATABASE_URL:
                auth_part = DATABASE_URL.split('://')[-1].split('@')[0]
                if ':' in auth_part:
                    error_msg = error_msg.replace(auth_part.split(':')[0], '[REDACTED]')
                    error_msg = error_msg.replace(auth_part.split(':')[1], '[REDACTED]')
        print(f"❌ 데이터베이스 연결 오류 (민감 정보 제거됨): {error_msg}", flush=True)
        raise

# ------------------------------------------------
# DB 초기화
# ------------------------------------------------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1️⃣ 유저 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        name TEXT,
        phone TEXT,
        gender TEXT CHECK(gender IN ('남','여','M','F')) NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    try:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT")
    except Exception:
        pass
    
    try:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT")
    except Exception:
        pass

    # 2️⃣ 샷 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS shots (
        id SERIAL PRIMARY KEY,
        store_id TEXT,
        bay_id TEXT,
        user_id TEXT,
        club_id TEXT,
        ball_speed REAL,
        club_speed REAL,
        launch_angle REAL,
        smash_factor REAL,
        face_angle REAL,
        club_path REAL,
        lateral_offset REAL,
        direction_angle REAL,
        side_spin INTEGER,
        back_spin INTEGER,
        total_distance REAL,
        carry REAL,
        feedback TEXT,
        timestamp TEXT
    )
    """)

    # shots 테이블 컬럼 추가
    for col in ["side_spin", "back_spin", "lateral_offset", "direction_angle", "total_distance", "carry"]:
        try:
            if col in ["side_spin", "back_spin"]:
                cur.execute(f"ALTER TABLE shots ADD COLUMN IF NOT EXISTS {col} INTEGER")
            else:
                cur.execute(f"ALTER TABLE shots ADD COLUMN IF NOT EXISTS {col} REAL")
        except Exception:
            pass

    # 3️⃣ 매장 테이블 (확장)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stores (
        store_id   TEXT PRIMARY KEY,
        store_name TEXT,
        admin_pw   TEXT,
        bays_count INTEGER,
        subscription_status TEXT DEFAULT 'active',
        subscription_start_date TEXT,
        subscription_end_date TEXT,
        payment_plan TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # stores 테이블 컬럼 추가
    for col in ["subscription_status", "subscription_start_date", "subscription_end_date", "payment_plan", "created_at"]:
        try:
            cur.execute(f"ALTER TABLE stores ADD COLUMN IF NOT EXISTS {col} TEXT")
        except Exception:
            pass

    # stores 테이블 컬럼 추가
    for col in ["subscription_status", "subscription_start_date", "subscription_end_date", "payment_plan", "created_at"]:
        try:
            cur.execute(f"ALTER TABLE stores ADD COLUMN IF NOT EXISTS {col} TEXT")
        except Exception:
            pass
    
    # stores 테이블에 status, requested_at, approved_at, approved_by 컬럼 추가
    try:
        cur.execute("ALTER TABLE stores ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending'")
    except Exception:
        pass
    
    try:
        cur.execute("ALTER TABLE stores ADD COLUMN IF NOT EXISTS requested_at TEXT DEFAULT CURRENT_TIMESTAMP")
    except Exception:
        pass
    
    try:
        cur.execute("ALTER TABLE stores ADD COLUMN IF NOT EXISTS approved_at TEXT")
    except Exception:
        pass
    
    try:
        cur.execute("ALTER TABLE stores ADD COLUMN IF NOT EXISTS approved_by TEXT")
    except Exception:
        pass

    # 4️⃣ 타석 테이블 (bay_number 추가, UNIQUE 제약조건)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bays (
        store_id    TEXT,
        bay_id      TEXT,
        bay_number  INTEGER,
        bay_name    TEXT,
        status      TEXT,
        user_id     TEXT,
        last_update TEXT,
        bay_code    TEXT UNIQUE,
        assigned_pc_unique_id TEXT,
        PRIMARY KEY (store_id, bay_id)
    )
    """)
    
    try:
        cur.execute("ALTER TABLE bays ADD COLUMN IF NOT EXISTS bay_code TEXT")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_bay_code ON bays(bay_code)")
    except Exception:
        pass
    
    # bay_number 컬럼 추가 (마이그레이션)
    try:
        cur.execute("ALTER TABLE bays ADD COLUMN IF NOT EXISTS bay_number INTEGER")
    except Exception:
        pass
    
    try:
        cur.execute("ALTER TABLE bays ADD COLUMN IF NOT EXISTS bay_name TEXT")
    except Exception:
        pass
    
    try:
        cur.execute("ALTER TABLE bays ADD COLUMN IF NOT EXISTS assigned_pc_unique_id TEXT")
    except Exception:
        pass
    
    # ✅ 1-2. 유니크 제약조건 (store_id, bay_number) 중복 방지
    try:
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_bays_store_baynumber
            ON bays(store_id, bay_number)
            WHERE bay_number IS NOT NULL
        """)
        print("[DB] bays 테이블 UNIQUE INDEX 생성 완료 (store_id, bay_number)")
    except Exception as e:
        print(f"[WARNING] bays UNIQUE INDEX 생성 실패 (이미 존재할 수 있음): {e}")

    # 5️⃣ 활성 세션 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS active_sessions (
        store_id    TEXT,
        bay_id      TEXT,
        user_id     TEXT,
        login_time  TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (store_id, bay_id)
    )
    """)

    # 6️⃣ 결제 테이블 (신규)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        store_id TEXT,
        amount REAL,
        payment_date TEXT,
        payment_method TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 7️⃣ 구독 테이블 (신규)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id SERIAL PRIMARY KEY,
        store_id TEXT,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'active',
        plan_type TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 8️⃣ 매장 PC 테이블 (신규)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS store_pcs (
        id SERIAL PRIMARY KEY,
        store_id TEXT,
        store_name TEXT NOT NULL,
        bay_id TEXT,
        bay_name TEXT NOT NULL,
        pc_name TEXT NOT NULL,
        pc_unique_id TEXT UNIQUE NOT NULL,
        pc_uuid TEXT,
        mac_address TEXT,
        pc_hostname TEXT,
        pc_platform TEXT,
        pc_info JSONB,
        pc_token TEXT UNIQUE,
        registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_seen_at TEXT,
        status TEXT DEFAULT 'pending',
        approved_at TEXT,
        approved_by TEXT,
        usage_start_date TEXT,
        usage_end_date TEXT,
        notes TEXT
    )
    """)
    
    # 기존 테이블에 새 컬럼 추가 (마이그레이션)
    for col in ["store_id", "bay_id", "pc_uuid", "mac_address", "pc_token"]:
        try:
            cur.execute(f"ALTER TABLE store_pcs ADD COLUMN IF NOT EXISTS {col} TEXT")
        except Exception as e:
            print(f"[WARNING] store_pcs {col} 컬럼 추가 실패 (이미 존재할 수 있음): {e}")
            conn.rollback()
    
    # bay_number 컬럼 추가 (INTEGER)
    try:
        cur.execute("ALTER TABLE store_pcs ADD COLUMN IF NOT EXISTS bay_number INTEGER")
        conn.commit()
        print("[DB] store_pcs 테이블에 bay_number 컬럼 추가 완료")
    except Exception as e:
        print(f"[WARNING] store_pcs bay_number 컬럼 추가 실패 (이미 존재할 수 있음): {e}")
        conn.rollback()
    
    try:
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pc_unique_id ON store_pcs(pc_unique_id)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pc_token ON store_pcs(pc_token) WHERE pc_token IS NOT NULL")
    except Exception:
        pass
    
    # ✅ 6. DB 레벨 보호: bay_id NOT NULL 및 중복 방지 인덱스
    try:
        # bay_id가 NULL인 경우를 허용하되, active 상태일 때는 NOT NULL 강제
        # PostgreSQL에서는 부분 인덱스로 처리
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_store_bay_id_active
            ON store_pcs (store_id, bay_id)
            WHERE status = 'active' AND bay_id IS NOT NULL
        """)
        print("[DB] bay_id 중복 방지 인덱스 생성 완료")
    except Exception as e:
        print(f"[WARNING] bay_id 인덱스 생성 실패 (이미 존재할 수 있음): {e}")
    
    # 주의: bay_id NOT NULL 제약조건은 기존 데이터가 NULL일 수 있으므로
    # 마이그레이션 스크립트로 별도 처리 필요 (기존 데이터 정리 후)

    # 9️⃣ PC 등록 코드 테이블 (신규)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pc_registration_codes (
        id SERIAL PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        issued_by TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        revoked_at TEXT,
        notes TEXT
    )
    """)
    
    try:
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_registration_code ON pc_registration_codes(code)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_registration_code_status ON pc_registration_codes(status)")
    except Exception:
        pass
    
    # 🔟 PC 연장 요청 테이블 (CRITICAL 2: 요청 기반 봉합)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pc_extension_requests (
        id SERIAL PRIMARY KEY,
        pc_id TEXT NOT NULL,
        pc_unique_id TEXT,
        store_id TEXT NOT NULL,
        requested_by TEXT NOT NULL,
        requested_until DATE,
        status TEXT DEFAULT 'REQUESTED' CHECK(status IN ('REQUESTED', 'APPROVED', 'REJECTED')),
        decided_by TEXT,
        decided_at TEXT,
        reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pc_unique_id) REFERENCES store_pcs(pc_unique_id) ON DELETE CASCADE
    )
    """)
    
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_extension_request_pc ON pc_extension_requests(pc_unique_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_extension_request_store ON pc_extension_requests(store_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_extension_request_status ON pc_extension_requests(status)")
    except Exception:
        pass
    
    # 1️⃣1️⃣ Audit 로그 테이블 (CRITICAL: 모든 중요 액션 기록)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id SERIAL PRIMARY KEY,
        actor_role TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL,
        target_type TEXT,
        target_id TEXT,
        before_state JSONB,
        after_state JSONB,
        ip_address TEXT,
        user_agent TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_role, actor_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_logs(target_type, target_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at)")
    except Exception:
        pass
    
    # 기존 테이블 마이그레이션 (pc_registration_keys → pc_registration_codes)
    # 주의: 이 마이그레이션은 데이터 마이그레이션이므로 유지 (seed 데이터 아님)
    try:
        cur.execute("""
            INSERT INTO pc_registration_codes (code, status, issued_by, created_at, notes)
            SELECT registration_key, 
                   CASE 
                       WHEN status = 'active' THEN 'ACTIVE'
                       ELSE 'REVOKED'
                   END,
                   created_by,
                   created_at,
                   notes
            FROM pc_registration_keys
            WHERE NOT EXISTS (
                SELECT 1 FROM pc_registration_codes WHERE code = pc_registration_keys.registration_key
            )
        """)
        conn.commit()
    except Exception:
        pass  # 테이블이 없으면 스킵

    # ⚠️ seed 데이터 생성 로직 제거됨
    # 기본 매장/타석 생성은 seed_dev_data.py 스크립트로 분리
    # 운영 환경에서는 절대 자동 실행되지 않음

    conn.commit()
    cur.close()
    conn.close()
    print("✅ DB 스키마 초기화 완료 (테이블/인덱스만 생성)")

# ------------------------------------------------
# 타석 코드 생성
# ------------------------------------------------
def generate_bay_code(store_id, bay_id, cursor=None):
    """타석 코드 생성 (4자리: 영문1자 + 숫자3자)
    
    Args:
        store_id: 매장 ID
        bay_id: 타석 ID
        cursor: 기존 DB 커서 (선택사항). 제공되면 해당 커서 사용, 없으면 새 연결 생성
    """
    import random
    import string
    
    # 매장 ID의 첫 글자 사용 (없으면 랜덤)
    if store_id and len(store_id) > 0:
        prefix = store_id[0].upper()
    else:
        prefix = random.choice(string.ascii_uppercase)
    
    # 숫자 3자리 (001-999)
    num = int(bay_id) if bay_id.isdigit() else random.randint(1, 999)
    suffix = f"{num:03d}"
    
    code = f"{prefix}{suffix}"
    
    # 중복 확인 (커서가 제공되면 사용, 아니면 새 연결 생성)
    if cursor:
        # 기존 커서 사용 (같은 트랜잭션 내)
        try:
            cursor.execute("SELECT COUNT(*) as count FROM bays WHERE bay_code = %s", (code,))
            count_result = cursor.fetchone()
            if count_result:
                # RealDictCursor는 딕셔너리, 일반 커서는 튜플 반환
                count = count_result.get('count', 0) if isinstance(count_result, dict) else count_result[0]
            else:
                count = 0
        except Exception:
            # 테이블이 아직 생성되지 않았으면 중복 확인 건너뛰기
            count = 0
    else:
        # 새 연결 생성
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) as count FROM bays WHERE bay_code = %s", (code,))
            count_result = cur.fetchone()
            if count_result:
                count = count_result.get('count', 0) if isinstance(count_result, dict) else count_result[0]
            else:
                count = 0
        except Exception:
            count = 0
        finally:
            cur.close()
            conn.close()
    
    if count > 0:
        # 중복이면 다른 코드 생성
        prefix = random.choice(string.ascii_uppercase)
        num = random.randint(1, 999)
        code = f"{prefix}{num:03d}"
    
    return code

# ------------------------------------------------
# 타석 코드로 매장/타석 조회
# ------------------------------------------------
def get_store_bay_by_code(bay_code):
    """타석 코드로 매장 ID와 타석 ID 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT store_id, bay_id FROM bays WHERE bay_code = %s",
        (bay_code.upper(),)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return dict(result) if result else None

# ------------------------------------------------
# 기존 함수들 (기존 database.py에서 가져옴)
# ------------------------------------------------

def login_user(user_id, password):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM users WHERE user_id=%s AND password=%s",
        (user_id, password)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return dict(user) if user else None

def get_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return dict(user) if user else None

def create_user(user_id, password, name=None, phone=None, gender=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (user_id, password, name, phone, gender) VALUES (%s, %s, %s, %s, %s)",
        (user_id, password, name, phone, gender)
    )
    conn.commit()
    cur.close()
    conn.close()

def check_user(user_id, password):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM users WHERE user_id=%s AND password=%s",
        (user_id, password)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return dict(user) if user else None

def save_shot_to_db(data):
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
INSERT INTO shots (
    store_id, bay_id, user_id, club_id,
    total_distance, carry,
    ball_speed, club_speed, launch_angle,
    smash_factor, face_angle, club_path,
    lateral_offset, direction_angle,
    side_spin, back_spin,
    feedback, timestamp
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
        data.get("store_id"),
        data.get("bay_id"),
        data.get("user_id"),
        data.get("club_id"),
        data.get("total_distance"),
        data.get("carry"),
        data.get("ball_speed"),
        data.get("club_speed"),
        data.get("launch_angle"),
        data.get("smash_factor"),
        data.get("face_angle"),
        data.get("club_path"),
        data.get("lateral_offset"),
        data.get("direction_angle"),
        data.get("side_spin"),
        data.get("back_spin"),
        data.get("feedback"),
        data.get("timestamp") or now
    ))
    conn.commit()
    cur.close()
    conn.close()

def get_last_shot(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM shots WHERE user_id=%s ORDER BY timestamp DESC LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None

def get_user_practice_dates(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT DISTINCT date(timestamp) AS d FROM shots WHERE user_id=%s ORDER BY d DESC
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_all_shots(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM shots WHERE user_id=%s ORDER BY timestamp DESC
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def set_active_session(store_id, bay_id, user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO active_sessions (store_id, bay_id, user_id, login_time)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (store_id, bay_id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            login_time = EXCLUDED.login_time
    """, (store_id, bay_id, user_id, now))
    conn.commit()
    cur.close()
    conn.close()

def clear_active_session(store_id, bay_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM active_sessions WHERE store_id = %s AND bay_id = %s
    """, (store_id, bay_id))
    conn.commit()
    deleted_count = cur.rowcount
    cur.close()
    conn.close()
    return deleted_count

def get_active_user(store_id, bay_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT user_id, login_time FROM active_sessions WHERE store_id = %s AND bay_id = %s
    """, (store_id, bay_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None

def get_bay_active_user_info(store_id, bay_id):
    return get_active_user(store_id, bay_id)

def check_store(store_id, password):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM stores WHERE store_id = %s AND admin_pw = %s",
        (store_id, password),
    )
    store = cur.fetchone()
    cur.close()
    conn.close()
    return dict(store) if store else None

def get_bays(store_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT bays_count FROM stores WHERE store_id = %s", (store_id,))
    store = cur.fetchone()
    if not store:
        return []
    bays_count = store["bays_count"]
    cur.execute("""
        SELECT * FROM bays WHERE store_id = %s ORDER BY bay_id
    """, (store_id,))
    all_bays = cur.fetchall()
    cur.close()
    conn.close()
    filtered_bays = []
    for bay in all_bays:
        bay_num = int(bay["bay_id"])
        if bay_num <= bays_count:
            filtered_bays.append(dict(bay))
    return filtered_bays

def get_all_shots_by_store(store_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM shots WHERE store_id = %s ORDER BY timestamp DESC LIMIT 100
    """, (store_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_shots_by_bay(store_id, bay_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM shots WHERE store_id = %s AND bay_id = %s ORDER BY timestamp DESC LIMIT 100
    """, (store_id, bay_id))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def create_store(store_id, store_name, password, bays_count):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM bays WHERE store_id = %s", (store_id,))
        cur.execute("""
            INSERT INTO stores (store_id, store_name, admin_pw, bays_count) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (store_id) DO UPDATE SET
                store_name = EXCLUDED.store_name,
                admin_pw = EXCLUDED.admin_pw,
                bays_count = EXCLUDED.bays_count
        """, (store_id, store_name, password, bays_count))
        for i in range(1, bays_count + 1):
            bay_id = f"{i:02d}"
            bay_code = generate_bay_code(store_id, bay_id, cur)
            cur.execute(
                "INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code) VALUES (%s, %s, 'READY', '', '', %s)",
                (store_id, bay_id, bay_code)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"매장 등록 오류: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_all_active_sessions(store_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT store_id, bay_id, user_id, login_time FROM active_sessions WHERE store_id = %s ORDER BY bay_id
    """, (store_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def clear_all_active_sessions(store_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM active_sessions WHERE store_id = %s", (store_id,))
    conn.commit()
    deleted_count = cur.rowcount
    cur.close()
    conn.close()
    return deleted_count

# ------------------------------------------------
# 매장 PC 관리
# ------------------------------------------------
def generate_pc_token(pc_unique_id, mac_address):
    """PC 전용 토큰 생성 (pc_live_xxxxx 형식)"""
    # PC 고유 ID와 MAC 주소를 조합하여 토큰 생성
    token_data = f"{pc_unique_id}:{mac_address}:{datetime.now().isoformat()}"
    token_hash = hashlib.sha256(token_data.encode()).hexdigest()[:16]
    return f"pc_live_{token_hash}"

def register_store_pc(store_name, bay_name, pc_name, pc_info):
    """매장 PC 등록 (승인 대기 상태)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        pc_unique_id = pc_info.get("unique_id")
        pc_uuid = pc_info.get("system_uuid") or pc_info.get("machine_guid")
        mac_address = pc_info.get("mac_address")
        pc_hostname = pc_info.get("hostname")
        pc_platform = pc_info.get("platform")
        
        # JSONB로 PC 정보 저장
        import json
        pc_info_json = json.dumps(pc_info)
        
        cur.execute("""
            INSERT INTO store_pcs (
                store_name, bay_name, pc_name, pc_unique_id,
                pc_uuid, mac_address, pc_hostname, pc_platform, 
                pc_info, last_seen_at, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'pending')
            ON CONFLICT (pc_unique_id) DO UPDATE SET
                store_name = EXCLUDED.store_name,
                bay_name = EXCLUDED.bay_name,
                pc_name = EXCLUDED.pc_name,
                pc_uuid = EXCLUDED.pc_uuid,
                mac_address = EXCLUDED.mac_address,
                pc_hostname = EXCLUDED.pc_hostname,
                pc_platform = EXCLUDED.pc_platform,
                pc_info = EXCLUDED.pc_info,
                last_seen_at = CURRENT_TIMESTAMP
                -- 상태는 승인된 경우에만 유지, 대기 상태면 그대로 유지
        """, (store_name, bay_name, pc_name, pc_unique_id, pc_uuid, mac_address, 
              pc_hostname, pc_platform, pc_info_json))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"PC 등록 오류: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False

def approve_pc(pc_unique_id, store_id, bay_id, approved_by):
    """PC 승인 및 토큰 발급"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # PC 정보 조회
        cur.execute("SELECT * FROM store_pcs WHERE pc_unique_id = %s", (pc_unique_id,))
        pc = cur.fetchone()
        
        if not pc:
            return None
        
        pc_dict = dict(pc)
        mac_address = pc_dict.get("mac_address", "")
        
        # 토큰 생성
        pc_token = generate_pc_token(pc_unique_id, mac_address)
        
        # 승인 및 토큰 발급
        cur.execute("""
            UPDATE store_pcs 
            SET status = 'active',
                store_id = %s,
                bay_id = %s,
                pc_token = %s,
                approved_at = CURRENT_TIMESTAMP,
                approved_by = %s
            WHERE pc_unique_id = %s
        """, (store_id, bay_id, pc_token, approved_by, pc_unique_id))
        
        conn.commit()
        
        # 업데이트된 정보 반환
        cur.execute("SELECT * FROM store_pcs WHERE pc_unique_id = %s", (pc_unique_id,))
        updated_pc = cur.fetchone()
        cur.close()
        conn.close()
        
        return dict(updated_pc) if updated_pc else None
    except Exception as e:
        print(f"PC 승인 오류: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return None

def verify_pc_token(pc_token):
    """PC 토큰 검증"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT * FROM store_pcs 
            WHERE pc_token = %s AND status = 'active'
        """, (pc_token,))
        pc = cur.fetchone()
        cur.close()
        conn.close()
        
        if pc:
            # last_seen_at 업데이트
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE store_pcs 
                SET last_seen_at = CURRENT_TIMESTAMP 
                WHERE pc_token = %s
            """, (pc_token,))
            conn.commit()
            cur.close()
            conn.close()
            
            return dict(pc)
        return None
    except Exception as e:
        print(f"토큰 검증 오류: {e}")
        return None

def get_store_pc_by_unique_id(pc_unique_id):
    """PC 고유번호로 PC 정보 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM store_pcs WHERE pc_unique_id = %s",
        (pc_unique_id,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return dict(result) if result else None

def get_store_pcs_by_store(store_name):
    """매장별 PC 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM store_pcs WHERE store_name = %s ORDER BY bay_name, pc_name",
        (store_name,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_all_store_pcs():
    """모든 매장 PC 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM store_pcs ORDER BY store_name, bay_name, pc_name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def update_pc_last_seen(pc_unique_id):
    """PC 마지막 접속 시간 업데이트"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE store_pcs SET last_seen_at = CURRENT_TIMESTAMP WHERE pc_unique_id = %s",
        (pc_unique_id,)
    )
    conn.commit()
    cur.close()
    conn.close()

# ------------------------------------------------
# PC 등록 코드 관리 (상태 기반: ACTIVE/REVOKED)
# ------------------------------------------------
def generate_registration_code(prefix="GOLF"):
    """PC 등록 코드 생성 (예: GOLF-1234)"""
    # 4자리 숫자 생성
    random_num = secrets.randbelow(10000)
    code = f"{prefix}-{random_num:04d}"
    return code

def create_registration_code(issued_by, notes=""):
    """PC 등록 코드 생성 및 저장 (기존 ACTIVE 코드는 REVOKED 처리)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 기존 ACTIVE 코드를 REVOKED로 변경
        cur.execute("""
            UPDATE pc_registration_codes 
            SET status = 'REVOKED', 
                revoked_at = CURRENT_TIMESTAMP
            WHERE status = 'ACTIVE'
        """)
        
        # 고유한 코드 생성 (중복 확인)
        max_attempts = 10
        code = None
        for _ in range(max_attempts):
            code = generate_registration_code()
            cur.execute("SELECT id FROM pc_registration_codes WHERE code = %s", (code,))
            if not cur.fetchone():
                break
        
        # 새 코드 생성 (ACTIVE)
        cur.execute("""
            INSERT INTO pc_registration_codes (
                code, status, issued_by, notes
            ) VALUES (%s, 'ACTIVE', %s, %s)
            RETURNING *
        """, (code, issued_by, notes))
        
        code_data = cur.fetchone()
        conn.commit()
        
        cur.close()
        conn.close()
        return dict(code_data) if code_data else None
    except Exception as e:
        print(f"등록 코드 생성 오류: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return None

def verify_registration_code(code):
    """PC 등록 코드 검증 (ACTIVE 코드만 허용, 복수 사용 가능)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT * FROM pc_registration_codes 
            WHERE code = %s AND status = 'ACTIVE'
        """, (code,))
        code_data = cur.fetchone()
        
        cur.close()
        conn.close()
        return dict(code_data) if code_data else None
    except Exception as e:
        print(f"등록 코드 검증 오류: {e}")
        return None

def get_all_registration_codes():
    """모든 등록 코드 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM pc_registration_codes ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def register_pc_with_code(registration_code, store_name, bay_name, pc_name, pc_info):
    """등록 코드로 PC 등록 및 토큰 발급 (복수 사용 허용)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 등록 코드 검증 (ACTIVE만 허용)
        code_data = verify_registration_code(registration_code)
        if not code_data:
            return None, "유효하지 않거나 폐기된 등록 코드입니다."
        
        code_id = code_data.get("id")
        
        # PC 정보 추출
        pc_unique_id = pc_info.get("unique_id")
        pc_uuid = pc_info.get("system_uuid") or pc_info.get("machine_guid")
        mac_address = pc_info.get("mac_address")
        pc_hostname = pc_info.get("hostname")
        pc_platform = pc_info.get("platform")
        
        # JSONB로 PC 정보 저장
        import json
        pc_info_json = json.dumps(pc_info)
        
        # PC 토큰 생성
        pc_token = generate_pc_token(pc_unique_id, mac_address)
        
        # PC 등록 (바로 활성화, 토큰 발급)
        # registered_code_id는 나중에 추가 가능 (현재는 코드 자체로 추적)
        cur.execute("""
            INSERT INTO store_pcs (
                store_name, bay_name, pc_name, pc_unique_id,
                pc_uuid, mac_address, pc_hostname, pc_platform,
                pc_info, pc_token, status, registered_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE', CURRENT_TIMESTAMP)
            ON CONFLICT (pc_unique_id) DO UPDATE SET
                store_name = EXCLUDED.store_name,
                bay_name = EXCLUDED.bay_name,
                pc_name = EXCLUDED.pc_name,
                pc_uuid = EXCLUDED.pc_uuid,
                mac_address = EXCLUDED.mac_address,
                pc_hostname = EXCLUDED.pc_hostname,
                pc_platform = EXCLUDED.pc_platform,
                pc_info = EXCLUDED.pc_info,
                pc_token = EXCLUDED.pc_token,
                status = 'ACTIVE',
                last_seen_at = CURRENT_TIMESTAMP
        """, (store_name, bay_name, pc_name, pc_unique_id, pc_uuid, mac_address,
              pc_hostname, pc_platform, pc_info_json, pc_token))
        
        conn.commit()
        
        # 등록된 PC 정보 조회
        cur.execute("SELECT * FROM store_pcs WHERE pc_unique_id = %s", (pc_unique_id,))
        pc_data = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if pc_data:
            return dict(pc_data), None
        else:
            return None, "PC 등록에 실패했습니다."
    except Exception as e:
        print(f"등록 코드로 PC 등록 오류: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        cur.close()
        conn.close()
        return None, str(e)

def get_all_stores():
    """모든 매장 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM stores ORDER BY store_id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_pending_stores():
    """승인 대기 중인 매장 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM stores WHERE status = 'pending' ORDER BY requested_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def approve_store(store_id, approved_by):
    """매장 승인 (타석 생성 포함) - 완전한 오류 처리 및 상세 메시지 반환"""
    conn = None
    cur = None
    
    try:
        # 1단계: 입력값 검증
        if not store_id:
            error_msg = "store_id가 없습니다."
            print(f"[ERROR] approve_store: {error_msg}")
            return (False, error_msg)
        if not approved_by:
            approved_by = "super_admin"
        
        # 2단계: 데이터베이스 연결
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
        except Exception as e:
            error_msg = f"데이터베이스 연결 실패: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return (False, error_msg)
        
        # 3단계: 스키마 마이그레이션 (필요한 컬럼 추가)
        try:
            cur.execute("ALTER TABLE stores ADD COLUMN IF NOT EXISTS approved_at TEXT")
            cur.execute("ALTER TABLE stores ADD COLUMN IF NOT EXISTS approved_by TEXT")
            conn.commit()
        except Exception as e:
            print(f"[WARN] 스키마 마이그레이션 중 오류 (계속 진행): {e}")
            conn.rollback()
        
        # 4단계: 매장 정보 조회
        try:
            cur.execute("SELECT * FROM stores WHERE store_id = %s", (store_id,))
            store = cur.fetchone()
            if not store:
                error_msg = f"매장을 찾을 수 없습니다. store_id={store_id}"
                print(f"[ERROR] approve_store: {error_msg}")
                return (False, error_msg)
        except Exception as e:
            error_msg = f"매장 정보 조회 실패: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return (False, error_msg)
        
        store = dict(store)
        bays_count = store.get("bays_count", 5)
        
        # bays_count 타입 변환 (TEXT로 저장된 경우)
        if isinstance(bays_count, str):
            try:
                bays_count = int(bays_count)
            except ValueError:
                bays_count = 5
        
        if not isinstance(bays_count, int) or bays_count < 1:
            bays_count = 5  # 기본값
        
        # 5단계: 매장 상태를 approved로 변경
        from datetime import datetime
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cur.execute("""
                UPDATE stores 
                SET status = 'approved',
                    approved_at = %s,
                    approved_by = %s
                WHERE store_id = %s
            """, (current_timestamp, approved_by, store_id))
        except Exception as e:
            error_msg = f"매장 상태 업데이트 실패: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return (False, error_msg)
        
        # 6단계: 기존 타석 삭제
        try:
            cur.execute("DELETE FROM bays WHERE store_id = %s", (store_id,))
        except Exception as e:
            print(f"[WARN] 기존 타석 삭제 중 오류 (계속 진행): {e}")
        
        # 7단계: 타석 생성
        created_bays = []
        for i in range(1, bays_count + 1):
            bay_id = f"{i:02d}"
            try:
                # bay_code 생성 (중복 방지)
                max_attempts = 10
                bay_code = None
                for attempt in range(max_attempts):
                    bay_code = generate_bay_code(store_id, bay_id, cur)
                    # 중복 확인 (RealDictCursor 사용 시 딕셔너리 반환)
                    cur.execute("SELECT COUNT(*) as count FROM bays WHERE bay_code = %s", (bay_code,))
                    count_result = cur.fetchone()
                    if count_result:
                        # RealDictCursor는 딕셔너리, 일반 커서는 튜플 반환
                        count_value = count_result.get('count', 0) if isinstance(count_result, dict) else count_result[0]
                        if count_value == 0:
                            break
                    if attempt == max_attempts - 1:
                        error_msg = f"타석 {bay_id}의 고유 코드 생성 실패 (중복, {max_attempts}회 시도)"
                        print(f"[ERROR] {error_msg}")
                        conn.rollback()
                        return (False, error_msg)
                
                # 타석 삽입 (ON CONFLICT 처리)
                try:
                    # 먼저 기존 타석이 있는지 확인 (RealDictCursor 사용 시 딕셔너리 반환)
                    cur.execute("SELECT COUNT(*) as count FROM bays WHERE store_id = %s AND bay_id = %s", (store_id, bay_id))
                    count_result = cur.fetchone()
                    existing_count = count_result.get('count', 0) if isinstance(count_result, dict) else (count_result[0] if count_result else 0)
                    
                    if existing_count > 0:
                        # 기존 타석 업데이트
                        cur.execute("""
                            UPDATE bays 
                            SET bay_code = %s,
                                status = 'READY'
                            WHERE store_id = %s AND bay_id = %s
                        """, (bay_code, store_id, bay_id))
                        # UPDATE는 rowcount가 0이어도 정상일 수 있음 (변경사항 없음)
                        created_bays.append(bay_id)
                        print(f"[DEBUG] 타석 {bay_id} 업데이트 성공 (bay_code={bay_code})")
                    else:
                        # 새 타석 삽입
                        cur.execute("""
                            INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code) 
                            VALUES (%s, %s, 'READY', '', '', %s)
                        """, (store_id, bay_id, bay_code))
                        
                        # INSERT는 rowcount가 1이어야 함
                        if cur.rowcount == 0:
                            error_msg = f"타석 {bay_id} 삽입 실패: rowcount=0 (bay_code={bay_code})"
                            print(f"[ERROR] {error_msg}")
                            import traceback
                            traceback.print_exc()
                            conn.rollback()
                            return (False, error_msg)
                        
                        created_bays.append(bay_id)
                        print(f"[DEBUG] 타석 {bay_id} 삽입 성공 (bay_code={bay_code})")
                    
                except psycopg2_errors.UniqueViolation as e:
                    # bay_code 중복인 경우 - 다른 코드로 재시도
                    error_detail = str(e)
                    print(f"[WARN] 타석 {bay_id} bay_code 중복 ({bay_code}), 재시도... 오류: {error_detail}")
                    # 다른 코드 생성
                    retry_success = False
                    for retry in range(5):
                        new_bay_code = generate_bay_code(store_id, bay_id, cur)
                        if new_bay_code != bay_code:
                            try:
                                cur.execute("""
                                    INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code) 
                                    VALUES (%s, %s, 'READY', '', '', %s)
                                """, (store_id, bay_id, new_bay_code))
                                if cur.rowcount > 0:
                                    created_bays.append(bay_id)
                                    print(f"[DEBUG] 타석 {bay_id} 생성 성공 (재시도, bay_code={new_bay_code})")
                                    retry_success = True
                                    break
                            except psycopg2_errors.UniqueViolation:
                                if retry == 4:
                                    error_msg = f"타석 {bay_id} 삽입 실패: bay_code 중복 (5회 재시도 실패, 마지막 시도: {new_bay_code})"
                                    print(f"[ERROR] {error_msg}")
                                    import traceback
                                    traceback.print_exc()
                                    conn.rollback()
                                    return (False, error_msg)
                                continue
                    
                    if not retry_success:
                        error_msg = f"타석 {bay_id} 삽입 실패: bay_code 중복 (재시도 실패)"
                        print(f"[ERROR] {error_msg}")
                        import traceback
                        traceback.print_exc()
                        conn.rollback()
                        return (False, error_msg)
                        
                except psycopg2_errors.NotNullViolation as e:
                    # 필수 컬럼 누락
                    error_msg = f"타석 {bay_id} 삽입 실패: 필수 컬럼 누락 - {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    import traceback
                    traceback.print_exc()
                    conn.rollback()
                    return (False, error_msg)
                except psycopg2.Error as e:
                    # 기타 PostgreSQL 오류
                    error_msg = f"타석 {bay_id} 삽입 실패: PostgreSQL 오류 - {type(e).__name__}: {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    import traceback
                    traceback.print_exc()
                    conn.rollback()
                    return (False, error_msg)
                
            except Exception as e:
                error_msg = f"타석 {bay_id} 생성 실패: 예외 발생 - {type(e).__name__}: {str(e)}"
                print(f"[ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
                conn.rollback()
                return (False, error_msg)
        
        # 8단계: 커밋
        try:
            conn.commit()
            print(f"[SUCCESS] 매장 승인 완료: {store_id}, 타석 {len(created_bays)}개 생성")
            return True
        except Exception as e:
            error_msg = f"커밋 실패: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return (False, error_msg)
        
    except psycopg2.IntegrityError as e:
        error_msg = f"데이터베이스 제약 조건 위반: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return (False, error_msg)
    except psycopg2.ProgrammingError as e:
        error_msg = f"SQL 구문 오류: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return (False, error_msg)
    except Exception as e:
        error_msg = f"매장 승인 오류: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return (False, error_msg)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def reject_store(store_id, approved_by):
    """매장 거부"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE stores 
            SET status = 'rejected',
                approved_at = CURRENT_TIMESTAMP,
                approved_by = %s
            WHERE store_id = %s
        """, (approved_by, store_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"매장 거부 오류: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def delete_store(store_id):
    """매장 삭제 (모든 관련 데이터 포함)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 먼저 매장 정보 조회 (store_name 확인용)
        cur.execute("SELECT store_id, store_name FROM stores WHERE store_id = %s", (store_id,))
        store_info = cur.fetchone()
        if not store_info:
            print(f"[WARNING] 매장 삭제 실패: store_id={store_id}가 존재하지 않습니다.")
            return False
        
        store_name = store_info[1] if len(store_info) > 1 else None
        print(f"[DEBUG] 매장 삭제 시작: store_id={store_id}, store_name={store_name}")
        
        # 관련 데이터 삭제 (순서 중요: 외래키 참조 제거)
        # store_pcs는 store_id 또는 store_name으로 저장될 수 있으므로 둘 다 확인
        cur.execute("DELETE FROM active_sessions WHERE store_id = %s", (store_id,))
        deleted_active_sessions = cur.rowcount
        
        cur.execute("DELETE FROM bays WHERE store_id = %s", (store_id,))
        deleted_bays = cur.rowcount
        
        cur.execute("DELETE FROM shots WHERE store_id = %s", (store_id,))
        deleted_shots = cur.rowcount
        
        # store_pcs: store_id 또는 store_name으로 삭제
        cur.execute("DELETE FROM store_pcs WHERE store_id = %s", (store_id,))
        deleted_pcs_by_id = cur.rowcount
        if store_name:
            cur.execute("DELETE FROM store_pcs WHERE store_name = %s", (store_name,))
            deleted_pcs_by_name = cur.rowcount
        else:
            deleted_pcs_by_name = 0
        
        print(f"[DEBUG] 매장 관련 데이터 삭제: active_sessions={deleted_active_sessions}, bays={deleted_bays}, shots={deleted_shots}, store_pcs (by_id)={deleted_pcs_by_id}, store_pcs (by_name)={deleted_pcs_by_name}")
        
        # 매장 삭제
        cur.execute("DELETE FROM stores WHERE store_id = %s", (store_id,))
        deleted_stores = cur.rowcount
        
        if deleted_stores == 0:
            print(f"[WARNING] 매장 삭제 실패: store_id={store_id}가 존재하지 않습니다.")
            conn.rollback()
            return False
        
        conn.commit()
        print(f"[DEBUG] 매장 삭제 완료: store_id={store_id}")
        return True
    except Exception as e:
        print(f"[ERROR] 매장 삭제 오류: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def delete_pc(pc_unique_id):
    """PC 삭제"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM store_pcs WHERE pc_unique_id = %s", (pc_unique_id,))
        conn.commit()
        deleted_count = cur.rowcount
        cur.close()
        conn.close()
        return deleted_count > 0
    except Exception as e:
        print(f"PC 삭제 오류: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False

# ------------------------------------------------
# PC 연장 요청 관리 (CRITICAL 2) - store_admin과 동일
# ------------------------------------------------
def create_extension_request(pc_unique_id, store_id, requested_by, requested_until, reason=None):
    """PC 연장 요청 생성"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 중복 요청 체크 (REQUESTED 상태인 요청이 있으면 실패)
        cur.execute("""
            SELECT id FROM pc_extension_requests 
            WHERE pc_unique_id = %s AND status = 'REQUESTED'
        """, (pc_unique_id,))
        existing = cur.fetchone()
        if existing:
            cur.close()
            conn.close()
            return None, "이미 대기 중인 연장 요청이 있습니다."
        
        # PC 정보 조회
        cur.execute("SELECT id, store_id FROM store_pcs WHERE pc_unique_id = %s", (pc_unique_id,))
        pc = cur.fetchone()
        if not pc:
            cur.close()
            conn.close()
            return None, "PC를 찾을 수 없습니다."
        
        pc_id = str(pc["id"])
        pc_store_id = pc.get("store_id") or store_id
        
        # 연장 요청 생성
        cur.execute("""
            INSERT INTO pc_extension_requests 
            (pc_id, pc_unique_id, store_id, requested_by, requested_until, reason, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'REQUESTED')
            RETURNING id
        """, (pc_id, pc_unique_id, pc_store_id, requested_by, requested_until, reason))
        
        request_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()
        
        return request_id, None
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return None, f"연장 요청 생성 실패: {str(e)}"

def get_extension_requests(store_id=None, pc_unique_id=None, status=None):
    """연장 요청 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        conditions = []
        params = []
        
        if store_id:
            conditions.append("er.store_id = %s")
            params.append(store_id)
        if pc_unique_id:
            conditions.append("er.pc_unique_id = %s")
            params.append(pc_unique_id)
        if status:
            conditions.append("er.status = %s")
            params.append(status)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cur.execute(f"""
            SELECT er.*, sp.pc_name, sp.bay_name, sp.bay_id
            FROM pc_extension_requests er
            LEFT JOIN store_pcs sp ON er.pc_unique_id = sp.pc_unique_id
            WHERE {where_clause}
            ORDER BY er.created_at DESC
        """, params)
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        cur.close()
        conn.close()
        return []

def approve_extension_request(request_id, decided_by, approved_until, reason=None):
    """연장 요청 승인"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 요청 조회
        cur.execute("SELECT * FROM pc_extension_requests WHERE id = %s", (request_id,))
        request = cur.fetchone()
        if not request:
            cur.close()
            conn.close()
            return False, "요청을 찾을 수 없습니다."
        
        if request["status"] != "REQUESTED":
            cur.close()
            conn.close()
            return False, "이미 처리된 요청입니다."
        
        pc_unique_id = request["pc_unique_id"]
        
        # PC 사용 기간 업데이트
        cur.execute("""
            UPDATE store_pcs 
            SET usage_end_date = %s,
                status = 'active'
            WHERE pc_unique_id = %s
        """, (approved_until, pc_unique_id))
        
        # 요청 상태 업데이트
        cur.execute("""
            UPDATE pc_extension_requests 
            SET status = 'APPROVED',
                decided_by = %s,
                decided_at = CURRENT_TIMESTAMP,
                reason = %s
            WHERE id = %s
        """, (decided_by, reason, request_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"승인 실패: {str(e)}"

def reject_extension_request(request_id, decided_by, reason=None):
    """연장 요청 반려"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 요청 조회
        cur.execute("SELECT * FROM pc_extension_requests WHERE id = %s", (request_id,))
        request = cur.fetchone()
        if not request:
            cur.close()
            conn.close()
            return False, "요청을 찾을 수 없습니다."
        
        if request["status"] != "REQUESTED":
            cur.close()
            conn.close()
            return False, "이미 처리된 요청입니다."
        
        # 요청 상태 업데이트
        cur.execute("""
            UPDATE pc_extension_requests 
            SET status = 'REJECTED',
                decided_by = %s,
                decided_at = CURRENT_TIMESTAMP,
                reason = %s
            WHERE id = %s
        """, (decided_by, reason, request_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False, f"반려 실패: {str(e)}"

# ------------------------------------------------
# Audit 로그 관리 (CRITICAL) - store_admin과 동일
# ------------------------------------------------
def log_audit(actor_role, actor_id, action, target_type=None, target_id=None, 
              before_state=None, after_state=None, ip_address=None, user_agent=None):
    """Audit 로그 기록"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        import json
        before_json = json.dumps(before_state) if before_state else None
        after_json = json.dumps(after_state) if after_state else None
        
        cur.execute("""
            INSERT INTO audit_logs 
            (actor_role, actor_id, action, target_type, target_id, 
             before_state, after_state, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (actor_role, actor_id, action, target_type, target_id, 
              before_json, after_json, ip_address, user_agent))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Audit 로그 기록 실패: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False
