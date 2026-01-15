# ===== shared/database.py (공유 데이터베이스 모듈) =====
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from urllib.parse import urlparse
import random
import string
import secrets
import hashlib

# PostgreSQL 연결 정보 (Railway 환경 변수 또는 로컬 설정)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/golf_data")

def get_db_connection():
    """PostgreSQL 데이터베이스 연결"""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")
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

    # 4️⃣ 타석 테이블 (코드 필드 추가)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bays (
        store_id    TEXT,
        bay_id      TEXT,
        status      TEXT,
        user_id     TEXT,
        last_update TEXT,
        bay_code    TEXT UNIQUE,
        PRIMARY KEY (store_id, bay_id)
    )
    """)
    
    try:
        cur.execute("ALTER TABLE bays ADD COLUMN IF NOT EXISTS bay_code TEXT")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_bay_code ON bays(bay_code)")
    except Exception:
        pass

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
        except Exception:
            pass
    
    try:
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pc_unique_id ON store_pcs(pc_unique_id)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pc_token ON store_pcs(pc_token) WHERE pc_token IS NOT NULL")
    except Exception:
        pass

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
    
    # 기존 테이블 마이그레이션 (pc_registration_keys → pc_registration_codes)
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

    # 기본 매장 생성
    cur.execute("SELECT COUNT(*) AS c FROM stores WHERE store_id = %s", ("gaja",))
    row = cur.fetchone()
    if not row or row[0] == 0:
        cur.execute(
            "INSERT INTO stores (store_id, store_name, admin_pw, bays_count) VALUES (%s, %s, %s, %s)",
            ("gaja", "가자골프", "1111", 5),
        )
        # 기본 타석 생성 (코드 포함)
        for i in range(1, 6):
            bay_id = f"{i:02d}"
            bay_code = generate_bay_code("gaja", bay_id, cur)
            cur.execute(
                """
                INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code)
                VALUES (%s, %s, 'READY', '', '', %s)
                ON CONFLICT (store_id, bay_id) DO NOTHING
                """,
                ("gaja", bay_id, bay_code),
            )
    else:
        cur.execute(
            "UPDATE stores SET admin_pw = %s WHERE store_id = %s",
            ("1111", "gaja")
        )
        cur.execute(
            "UPDATE stores SET bays_count = %s WHERE store_id = %s AND bays_count > %s",
            (5, "gaja", 5)
        )
        # 기존 타석에 코드 부여 (없는 경우)
        for i in range(1, 6):
            bay_id = f"{i:02d}"
            cur.execute("SELECT bay_code FROM bays WHERE store_id = %s AND bay_id = %s", ("gaja", bay_id))
            existing = cur.fetchone()
            if not existing or not existing[0]:
                bay_code = generate_bay_code("gaja", bay_id, cur)
                cur.execute(
                    "UPDATE bays SET bay_code = %s WHERE store_id = %s AND bay_id = %s",
                    (bay_code, "gaja", bay_id)
                )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ DB 준비 완료")

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
            cursor.execute("SELECT COUNT(*) FROM bays WHERE bay_code = %s", (code,))
            count = cursor.fetchone()[0]
        except Exception:
            # 테이블이 아직 생성되지 않았으면 중복 확인 건너뛰기
            count = 0
    else:
        # 새 연결 생성
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM bays WHERE bay_code = %s", (code,))
            count = cur.fetchone()[0]
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
                    # 중복 확인
                    cur.execute("SELECT COUNT(*) FROM bays WHERE bay_code = %s", (bay_code,))
                    count_result = cur.fetchone()
                    if count_result and count_result[0] == 0:
                        break
                    if attempt == max_attempts - 1:
                        error_msg = f"타석 {bay_id}의 고유 코드 생성 실패 (중복, {max_attempts}회 시도)"
                        print(f"[ERROR] {error_msg}")
                        conn.rollback()
                        return (False, error_msg)
                
                # 타석 삽입 (ON CONFLICT 처리)
                try:
                    # 먼저 기존 타석이 있는지 확인
                    cur.execute("SELECT COUNT(*) FROM bays WHERE store_id = %s AND bay_id = %s", (store_id, bay_id))
                    existing_count = cur.fetchone()[0]
                    
                    if existing_count > 0:
                        # 기존 타석 업데이트
                        cur.execute("""
                            UPDATE bays 
                            SET bay_code = %s,
                                status = 'READY'
                            WHERE store_id = %s AND bay_id = %s
                        """, (bay_code, store_id, bay_id))
                    else:
                        # 새 타석 삽입
                        cur.execute("""
                            INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code) 
                            VALUES (%s, %s, 'READY', '', '', %s)
                        """, (store_id, bay_id, bay_code))
                    
                    # 삽입/업데이트 확인
                    if cur.rowcount == 0:
                        error_msg = f"타석 {bay_id} 삽입/업데이트 실패: rowcount=0 (bay_code={bay_code})"
                        print(f"[ERROR] {error_msg}")
                        import traceback
                        traceback.print_exc()
                        conn.rollback()
                        return (False, error_msg)
                    
                    created_bays.append(bay_id)
                    print(f"[DEBUG] 타석 {bay_id} 생성 성공 (bay_code={bay_code})")
                    
                except psycopg2.errors.UniqueViolation as e:
                    # bay_code 중복인 경우 - 다른 코드로 재시도
                    print(f"[WARN] 타석 {bay_id} bay_code 중복 ({bay_code}), 재시도...")
                    # 다른 코드 생성
                    for retry in range(5):
                        new_bay_code = generate_bay_code(store_id, bay_id, cur)
                        if new_bay_code != bay_code:
                            try:
                                cur.execute("""
                                    INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code) 
                                    VALUES (%s, %s, 'READY', '', '', %s)
                                """, (store_id, bay_id, new_bay_code))
                                created_bays.append(bay_id)
                                print(f"[DEBUG] 타석 {bay_id} 생성 성공 (재시도, bay_code={new_bay_code})")
                                break
                            except psycopg2.errors.UniqueViolation:
                                if retry == 4:
                                    error_msg = f"타석 {bay_id} 삽입 실패: bay_code 중복 (5회 재시도 실패)"
                                    print(f"[ERROR] {error_msg}")
                                    import traceback
                                    traceback.print_exc()
                                    conn.rollback()
                                    return (False, error_msg)
                                continue
                    else:
                        error_msg = f"타석 {bay_id} 삽입 실패: bay_code 중복 (재시도 실패)"
                        print(f"[ERROR] {error_msg}")
                        import traceback
                        traceback.print_exc()
                        conn.rollback()
                        return (False, error_msg)
                        
                except psycopg2.errors.NotNullViolation as e:
                    # 필수 컬럼 누락
                    error_msg = f"타석 {bay_id} 삽입 실패: 필수 컬럼 누락 - {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    import traceback
                    traceback.print_exc()
                    conn.rollback()
                    return (False, error_msg)
                except psycopg2.Error as e:
                    # 기타 PostgreSQL 오류
                    error_msg = f"타석 {bay_id} 삽입 실패: PostgreSQL 오류 - {str(e)}"
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
        # 관련 데이터 삭제 (순서 중요: 외래키 참조 제거)
        cur.execute("DELETE FROM active_sessions WHERE store_id = %s", (store_id,))
        cur.execute("DELETE FROM bays WHERE store_id = %s", (store_id,))
        cur.execute("DELETE FROM shots WHERE store_id = %s", (store_id,))
        cur.execute("DELETE FROM store_pcs WHERE store_id = %s", (store_id,))
        
        # 매장 삭제
        cur.execute("DELETE FROM stores WHERE store_id = %s", (store_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"매장 삭제 오류: {e}")
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
