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
    
    # stores 테이블에 매장 정보 컬럼 추가
    for col in ["contact", "business_number", "owner_name", "birth_date", "email", "address"]:
        try:
            cur.execute(f"ALTER TABLE stores ADD COLUMN IF NOT EXISTS {col} TEXT")
        except Exception:
            pass
    
    # stores 테이블에 status와 requested_at 컬럼 추가 (매장 등록 요청용)
    for col in ["status", "requested_at"]:
        try:
            cur.execute(f"ALTER TABLE stores ADD COLUMN IF NOT EXISTS {col} TEXT")
        except Exception:
            pass

    # 4️⃣ 타석 테이블 (코드 필드 추가)
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
    
    # ✅ UNIQUE 제약조건 (store_id, bay_number) 중복 방지
    try:
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_bays_store_baynumber
            ON bays(store_id, bay_number)
            WHERE bay_number IS NOT NULL
        """)
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
    """매장의 전체 타석 목록 조회 (PC 등록 상태 및 유효성 포함)"""
    from datetime import date
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 매장 정보 조회
    cur.execute("SELECT bays_count, store_name FROM stores WHERE store_id = %s", (store_id,))
    store = cur.fetchone()
    if not store:
        return []
    
    bays_count = store["bays_count"]
    store_name = store.get("store_name", "")
    today = date.today()
    
    # 전체 타석 조회 (bays_count만큼)
    all_bays = []
    for i in range(1, bays_count + 1):
        bay_id = f"{i:02d}"
        bay_dict = {
            "store_id": store_id,
            "bay_id": bay_id,
            "status": "READY",
            "user_id": "",
            "last_update": "",
            "bay_code": None,
            "has_pc": False,
            "is_valid": False,
            "pc_status": None,
            "pc_name": None
        }
        all_bays.append(bay_dict)
    
    # DB에 저장된 타석 정보 조회
    cur.execute("""
        SELECT * FROM bays WHERE store_id = %s ORDER BY bay_id
    """, (store_id,))
    db_bays = cur.fetchall()
    
    # DB 타석 정보로 업데이트
    for db_bay in db_bays:
        bay_id = db_bay["bay_id"]
        bay_num = int(bay_id)
        if bay_num <= bays_count:
            for bay in all_bays:
                if bay["bay_id"] == bay_id:
                    bay.update(dict(db_bay))
                    break
    
    # 각 타석의 PC 등록 상태 및 유효성 확인 (bay_id 포함)
    cur.execute("""
        SELECT bay_id, bay_name, pc_name, status, usage_end_date, approved_at
        FROM store_pcs
        WHERE store_name = %s
    """, (store_name,))
    pcs = cur.fetchall()
    
    # 각 타석의 PC 등록 상태 및 유효성 확인 (bay_id 우선 사용)
    import re
    for pc in pcs:
        # 1. bay_id가 있으면 우선 사용
        pc_bay_id = pc.get("bay_id")
        if pc_bay_id and str(pc_bay_id).strip().isdigit():
            try:
                pc_bay_num = int(pc_bay_id)
                if 1 <= pc_bay_num <= bays_count:
                    bay_id = f"{pc_bay_num:02d}"
                    for bay in all_bays:
                        if bay["bay_id"] == bay_id:
                            bay["has_pc"] = True
                            bay["pc_status"] = pc.get("status")
                            bay["pc_name"] = pc.get("pc_name")
                            # 유효성 판정: status='active'이고 사용 기간이 유효한 경우
                            if pc.get("status") == "active":
                                usage_end_date = pc.get("usage_end_date")
                                if usage_end_date:
                                    if isinstance(usage_end_date, str):
                                        from datetime import datetime
                                        try:
                                            usage_end_date = datetime.strptime(usage_end_date, "%Y-%m-%d").date()
                                        except:
                                            usage_end_date = None
                                    if usage_end_date and usage_end_date >= today:
                                        bay["is_valid"] = True
                                else:
                                    # 사용 기간이 없으면 무제한으로 간주
                                    bay["is_valid"] = True
                            break
                    continue  # bay_id로 매칭했으면 다음 PC로
            except (ValueError, TypeError):
                pass
        
        # 2. bay_id가 없으면 bay_name에서 추출
        bay_name = pc.get("bay_name", "")
        if bay_name:
            # "1번룸", "01번 타석", "1타석", "테스트매장-1번룸-PC" 등에서 숫자 추출
            # 패턴: 숫자 뒤에 "번" 또는 숫자만 있는 경우
            match = re.search(r'(\d+)\s*번|^(\d+)(?=\s|$)', str(bay_name))
            if match:
                pc_bay_num = int(match.group(1) or match.group(2))
                if 1 <= pc_bay_num <= bays_count:
                    bay_id = f"{pc_bay_num:02d}"
                    for bay in all_bays:
                        if bay["bay_id"] == bay_id:
                            bay["has_pc"] = True
                            bay["pc_status"] = pc.get("status")
                            bay["pc_name"] = pc.get("pc_name")
                            # 유효성 판정: status='active'이고 사용 기간이 유효한 경우
                            if pc.get("status") == "active":
                                usage_end_date = pc.get("usage_end_date")
                                if usage_end_date:
                                    if isinstance(usage_end_date, str):
                                        from datetime import datetime
                                        try:
                                            usage_end_date = datetime.strptime(usage_end_date, "%Y-%m-%d").date()
                                        except:
                                            usage_end_date = None
                                    if usage_end_date and usage_end_date >= today:
                                        bay["is_valid"] = True
                                else:
                                    # 사용 기간이 없으면 무제한으로 간주
                                    bay["is_valid"] = True
                            break
    
    cur.close()
    conn.close()
    return all_bays

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

def create_store(store_id, store_name, password, contact=None, business_number=None, owner_name=None, birth_date=None, email=None, address=None, bays_count=1):
    """
    매장 등록 함수 - 완전한 오류 처리 및 검증 포함
    """
    conn = None
    cur = None
    
    # 1단계: 입력값 검증
    try:
        store_id = str(store_id).upper().strip() if store_id else ""
        store_name = str(store_name).strip() if store_name else ""
        password = str(password).strip() if password else ""
        
        if not store_id:
            return False, "매장코드를 입력해주세요."
        if not store_name:
            return False, "매장명을 입력해주세요."
        if not password:
            return False, "비밀번호를 입력해주세요."
        if not isinstance(bays_count, int) or bays_count < 1 or bays_count > 50:
            return False, "타석(룸) 수는 1개 이상 50개 이하여야 합니다."
        
        # None 값 처리 (안전하게)
        contact = str(contact).strip() if contact else None
        business_number = str(business_number).strip() if business_number else None
        owner_name = str(owner_name).strip() if owner_name else None
        birth_date = str(birth_date).strip() if birth_date else None
        email = str(email).strip() if email else None
        address = str(address).strip() if address else None
        
    except Exception as e:
        return False, f"입력값 검증 오류: {str(e)}"
    
    # 2단계: 데이터베이스 연결
    try:
        conn = get_db_connection()
        cur = conn.cursor()
    except Exception as e:
        error_msg = f"데이터베이스 연결 실패: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    
    # 3단계: 테이블 스키마 확인 및 마이그레이션
    try:
        # stores 테이블에 필요한 컬럼이 있는지 확인하고 추가
        required_columns = {
            "status": "TEXT",
            "requested_at": "TEXT",
            "contact": "TEXT",
            "business_number": "TEXT",
            "owner_name": "TEXT",
            "birth_date": "TEXT",
            "email": "TEXT",
            "address": "TEXT"
        }
        
        for col_name, col_type in required_columns.items():
            try:
                cur.execute(f"ALTER TABLE stores ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
            except Exception as e:
                # 컬럼이 이미 존재하거나 다른 오류 (무시 가능)
                pass
        
        conn.commit()
    except Exception as e:
        print(f"[WARN] 스키마 마이그레이션 중 오류 (계속 진행): {e}")
        conn.rollback()
    
    # 4단계: 트랜잭션 시작
    try:
        # 기존 타석 삭제 (트랜잭션 내에서)
        try:
            cur.execute("DELETE FROM bays WHERE store_id = %s", (store_id,))
        except Exception as e:
            print(f"[WARN] 기존 타석 삭제 중 오류 (계속 진행): {e}")
        
        # 매장 정보 삽입/업데이트
        # PostgreSQL에서 CURRENT_TIMESTAMP는 TIMESTAMP를 반환하므로 TEXT로 변환
        from datetime import datetime
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 기존 매장 상태 확인
        cur.execute("SELECT status, requested_at FROM stores WHERE store_id = %s", (store_id,))
        existing_store = cur.fetchone()
        
        # 매장 정보 삽입/업데이트
        # ON CONFLICT에서 CASE 문을 사용하여 기존 상태 유지
        cur.execute("""
            INSERT INTO stores (
                store_id, store_name, admin_pw, bays_count, 
                contact, business_number, owner_name, birth_date, email, address, 
                status, requested_at
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
            ON CONFLICT (store_id) DO UPDATE SET
                store_name = EXCLUDED.store_name,
                admin_pw = EXCLUDED.admin_pw,
                bays_count = EXCLUDED.bays_count,
                contact = EXCLUDED.contact,
                business_number = EXCLUDED.business_number,
                owner_name = EXCLUDED.owner_name,
                birth_date = EXCLUDED.birth_date,
                email = EXCLUDED.email,
                address = EXCLUDED.address,
                status = CASE 
                    WHEN stores.status = 'approved' THEN 'approved'
                    ELSE 'pending'
                END,
                requested_at = CASE 
                    WHEN stores.status = 'approved' THEN stores.requested_at
                    ELSE %s
                END
        """, (
            store_id, store_name, password, bays_count,
            contact, business_number, owner_name, birth_date, email, address,
            current_timestamp,  # INSERT의 requested_at
            current_timestamp   # UPDATE의 requested_at (새 요청인 경우)
        ))
        
        # 5단계: 타석 생성
        created_bays = []
        for i in range(1, bays_count + 1):
            bay_id = f"{i:02d}"
            try:
                # bay_code 생성 (중복 방지 포함)
                max_attempts = 10
                bay_code = None
                for attempt in range(max_attempts):
                    bay_code = generate_bay_code(store_id, bay_id, cur)
                    # 중복 확인
                    cur.execute("SELECT COUNT(*) FROM bays WHERE bay_code = %s", (bay_code,))
                    if cur.fetchone()[0] == 0:
                        break
                    if attempt == max_attempts - 1:
                        return False, f"타석 {bay_id}의 고유 코드 생성 실패 (중복)"
                
                # 타석 삽입
                cur.execute("""
                    INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code) 
                    VALUES (%s, %s, 'READY', '', '', %s)
                    ON CONFLICT (store_id, bay_id) DO UPDATE SET 
                        bay_code = EXCLUDED.bay_code,
                        status = 'READY'
                """, (store_id, bay_id, bay_code))
                
                created_bays.append(bay_id)
            except Exception as e:
                error_msg = f"타석 {bay_id} 생성 실패: {str(e)}"
                print(f"[ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
                conn.rollback()
                return False, error_msg
        
        # 6단계: 커밋
        conn.commit()
        print(f"[SUCCESS] 매장 등록 완료: {store_id}, 타석 {len(created_bays)}개 생성")
        return True
        
    except psycopg2.IntegrityError as e:
        error_msg = f"데이터베이스 제약 조건 위반: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False, error_msg
    except psycopg2.ProgrammingError as e:
        error_msg = f"SQL 구문 오류: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False, error_msg
    except Exception as e:
        error_msg = f"매장 등록 오류: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False, error_msg
    finally:
        if cur:
            cur.close()
        if conn:
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
    """매장별 PC 목록 조회 (bay_id 포함)"""
    if not store_name:
        return []
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # store_pcs 테이블에서 모든 필드 조회 (단순 쿼리)
        cur.execute("""
            SELECT sp.*
            FROM store_pcs sp
            WHERE sp.store_name = %s 
            ORDER BY sp.registered_at DESC
        """, (store_name,))
        rows = cur.fetchall()
        
        # bay_id가 없으면 bay_name에서 추출
        import re
        result = []
        for row in rows:
            try:
                pc = dict(row)
                # bay_id가 없거나 숫자가 아니면 bay_name에서 추출
                bay_id = pc.get("bay_id")
                if not bay_id or not str(bay_id).strip().isdigit():
                    bay_name = pc.get("bay_name", "")
                    if bay_name:
                        # "1번룸", "01번 타석", "1타석", "테스트매장-1번룸-PC" 등에서 숫자 추출
                        # 패턴: 숫자 뒤에 "번" 또는 숫자만 있는 경우
                        match = re.search(r'(\d+)\s*번|^(\d+)(?=\s|$)', str(bay_name))
                        if match:
                            bay_num = int(match.group(1) or match.group(2))
                            pc["bay_id"] = f"{bay_num:02d}"
                result.append(pc)
            except Exception as e:
                print(f"PC 데이터 처리 오류: {e}")
                continue
        
        # Python에서 bay_id 기준으로 정렬
        def sort_key(pc):
            bay_id = pc.get("bay_id", "")
            try:
                if bay_id and str(bay_id).strip().isdigit():
                    return int(bay_id)
                return 999
            except:
                return 999
        
        result.sort(key=sort_key)
        
        return result
    except Exception as e:
        print(f"get_store_pcs_by_store 오류: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cur.close()
        conn.close()

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

def get_store_by_id(store_id):
    """매장코드로 매장 정보 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM stores WHERE store_id = %s", (store_id,))
    store = cur.fetchone()
    cur.close()
    conn.close()
    return dict(store) if store else None

def check_store_id_exists(store_id):
    """매장코드 중복 확인"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stores WHERE store_id = %s", (store_id,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0

def has_valid_pc_for_store(store_id):
    """매장에 유효한 PC가 하나라도 있는지 확인"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    today = date.today()
    
    cur.execute("""
        SELECT COUNT(*) as count
        FROM store_pcs
        WHERE store_id = %s
          AND status = 'active'
          AND (usage_end_date IS NULL OR usage_end_date >= %s)
    """, (store_id, today))
    
    result = cur.fetchone()
    count = result['count'] if result else 0
    
    cur.close()
    conn.close()
    
    return count > 0

# ------------------------------------------------
# PC 연장 요청 관리 (CRITICAL 2)
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
# Audit 로그 관리 (CRITICAL)
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

def get_pc_status_summary(store_id):
    """매장의 PC 상태 요약 (유효 개수, 전체 개수, 마지막 만료일)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    today = date.today()
    
    cur.execute("""
        SELECT
            COUNT(*) FILTER (
                WHERE status = 'active'
                  AND (usage_end_date IS NULL OR usage_end_date >= %s)
            ) AS valid_count,
            COUNT(*) AS total_count,
            MAX(usage_end_date) AS last_expiry
        FROM store_pcs
        WHERE store_id = %s
    """, (today, store_id))
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    return dict(result) if result else {"valid_count": 0, "total_count": 0, "last_expiry": None}
