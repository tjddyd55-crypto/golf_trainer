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
    
    try:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date TEXT")
    except Exception:
        pass
    
    # phone 컬럼에 UNIQUE 제약조건 추가 (중복 가입 방지)
    try:
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'users_phone_unique'
                ) THEN
                    ALTER TABLE users ADD CONSTRAINT users_phone_unique UNIQUE (phone);
                END IF;
            END $$;
        """)
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
    
    # is_guest 컬럼 추가 (게스트 샷 정책 명문화)
    try:
        cur.execute("ALTER TABLE shots ADD COLUMN IF NOT EXISTS is_guest BOOLEAN DEFAULT FALSE")
    except Exception:
        pass
    
    # is_valid, score 컬럼 추가 (샷 데이터 분석 구조)
    try:
        cur.execute("ALTER TABLE shots ADD COLUMN IF NOT EXISTS is_valid BOOLEAN DEFAULT FALSE")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE shots ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT NULL")
    except Exception:
        pass
    
    # shots 테이블 인덱스 추가 (7일 평균 계산 성능 향상)
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_shots_user_timestamp ON shots(user_id, timestamp)")
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

def create_user(user_id, password, name=None, phone=None, gender=None, birth_date=None):
    """유저 생성 (휴대폰번호 중복 체크 포함)"""
    import psycopg2
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 휴대폰번호 중복 체크
        if phone:
            cur.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
            existing = cur.fetchone()
            if existing:
                cur.close()
                conn.close()
                raise ValueError(f"이미 등록된 휴대폰번호입니다: {phone}")
        
        cur.execute(
            "INSERT INTO users (user_id, password, name, phone, gender, birth_date) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, password, name, phone, gender, birth_date)
        )
        conn.commit()
        cur.close()
        conn.close()
    except psycopg2.IntegrityError as e:
        conn.rollback()
        cur.close()
        conn.close()
        if "users_phone_unique" in str(e):
            raise ValueError(f"이미 등록된 휴대폰번호입니다: {phone}")
        raise

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
    """
    샷 데이터 저장 (최근 샷 10분 기준 active_user 판단)
    
    active_user는 최근 샷으로만 유지된다.
    최근 샷이 10분간 없으면 자동 로그아웃 처리된다.
    프로그램 생존 여부는 판단 기준이 아니다.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    store_id = data.get("store_id")
    bay_id = data.get("bay_id")
    
    # 최근 샷 10분 기준으로 active_user 유효성 확인
    from datetime import timedelta
    ttl_minutes = 10
    ttl_time = datetime.now() - timedelta(minutes=ttl_minutes)
    ttl_time_str = ttl_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 해당 타석의 최근 샷 시간 확인 (user_id가 있고 게스트가 아닌 샷)
    cur.execute("""
        SELECT MAX(timestamp) as last_shot_time
        FROM shots
        WHERE store_id = %s 
          AND bay_id = %s
          AND user_id IS NOT NULL 
          AND user_id != '' 
          AND (is_guest = FALSE OR is_guest IS NULL)
    """, (store_id, bay_id))
    
    last_shot_row = cur.fetchone()
    last_shot_time = last_shot_row.get("last_shot_time") if last_shot_row else None
    
    # active_user 확인 (bays 테이블)
    cur.execute("""
        SELECT user_id, last_update as login_time 
        FROM bays 
        WHERE store_id = %s AND bay_id = %s AND user_id IS NOT NULL AND user_id != ''
    """, (store_id, bay_id))
    active_user_row = cur.fetchone()
    active_user_id = active_user_row.get("user_id") if active_user_row else None
    
    # 최근 샷 10분 기준으로 active_user 판단
    user_id = None
    is_guest = True
    
    if active_user_id and last_shot_time:
        # timestamp 문자열 비교 (YYYY-MM-DD HH:MM:SS 형식)
        if last_shot_time >= ttl_time_str:
            # 최근 샷이 10분 이내면 active_user 유지
            user_id = active_user_id
            is_guest = False
            print(f"[INFO] 개인 샷 저장: store_id={store_id}, bay_id={bay_id}, user_id={user_id} (최근 샷 {last_shot_time} 기준)")
        else:
            # 최근 샷이 10분 초과면 active_user 해제하고 게스트 샷으로 저장
            cur.execute("""
                UPDATE bays SET user_id = '', last_update = CURRENT_TIMESTAMP
                WHERE store_id = %s AND bay_id = %s
            """, (store_id, bay_id))
            cur.execute("DELETE FROM active_sessions WHERE store_id = %s AND bay_id = %s", (store_id, bay_id))
            user_id = None
            is_guest = True
            print(f"[INFO] active_user 자동 해제 후 게스트 샷 저장: store_id={store_id}, bay_id={bay_id} (최근 샷 {last_shot_time}, {ttl_minutes}분 초과)")
    elif active_user_id and not last_shot_time:
        # active_user는 있지만 최근 샷이 없으면 해제하고 게스트 샷
        cur.execute("""
            UPDATE bays SET user_id = '', last_update = CURRENT_TIMESTAMP
            WHERE store_id = %s AND bay_id = %s
        """, (store_id, bay_id))
        cur.execute("DELETE FROM active_sessions WHERE store_id = %s AND bay_id = %s", (store_id, bay_id))
        user_id = None
        is_guest = True
        print(f"[INFO] active_user 자동 해제 후 게스트 샷 저장: store_id={store_id}, bay_id={bay_id} (최근 샷 없음)")
    else:
        # active_user가 없으면 게스트 샷
        user_id = None
        is_guest = True
        print(f"[INFO] 게스트 샷 저장: store_id={store_id}, bay_id={bay_id}")
    
    # criteria.json 기준으로 샷 평가 (is_valid, score 계산, 성별 기준 적용)
    try:
        import sys
        import os
        # utils.py 경로 추가 (services/user/utils.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        user_dir = os.path.dirname(current_dir)  # services/user/
        if user_dir not in sys.path:
            sys.path.insert(0, user_dir)
        from utils import evaluate_shot_by_criteria, get_criteria_key
        
        # 유저 성별 조회 (성별 없으면 male 기준)
        gender = None
        if user_id:
            user = get_user(user_id)
            if user:
                gender = user.get("gender")
        
        club_id = data.get("club_id") or ""
        # criteria 키 결정 로그 (초기 점검용)
        criteria_key = get_criteria_key(club_id, gender)
        print(f"[CRITERIA] club={club_id}, gender={gender} → key={criteria_key}")
        
        is_valid, score = evaluate_shot_by_criteria(data, club_id, gender=gender)
    except Exception as e:
        print(f"[WARNING] 샷 평가 실패: {e}")
        import traceback
        traceback.print_exc()
        is_valid = False
        score = 0
    
    cur.execute("""
INSERT INTO shots (
    store_id, bay_id, user_id, club_id,
    total_distance, carry,
    ball_speed, club_speed, launch_angle,
    smash_factor, face_angle, club_path,
    lateral_offset, direction_angle,
    side_spin, back_spin,
    feedback, timestamp, is_guest, is_valid, score
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
        store_id,
        bay_id,
        user_id,  # 게스트일 경우 NULL
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
        data.get("timestamp") or now,
        is_guest,  # 게스트 샷 표시
        is_valid,  # 기준 충족 여부
        score  # 점수 (0-100)
    ))
    conn.commit()
    cur.close()
    conn.close()

def get_last_shot(user_id):
    """개인 유저의 마지막 샷 조회 (게스트 샷 절대 제외)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM shots 
        WHERE user_id = %s 
          AND user_id IS NOT NULL 
          AND user_id != '' 
          AND (is_guest = FALSE OR is_guest IS NULL)
        ORDER BY timestamp DESC LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None

def get_user_practice_dates(user_id):
    """개인 유저의 연습 날짜 목록 조회 (게스트 샷 절대 제외)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT DISTINCT date(timestamp) AS d 
        FROM shots 
        WHERE user_id = %s 
          AND user_id IS NOT NULL 
          AND user_id != '' 
          AND (is_guest = FALSE OR is_guest IS NULL)
        ORDER BY d DESC
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_all_shots(user_id):
    """개인 유저의 샷 목록 조회 (게스트 샷 절대 제외)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # 게스트 샷 제외: user_id가 정확히 일치하고, is_guest가 FALSE이거나 NULL인 경우만 조회
    cur.execute("""
        SELECT * FROM shots 
        WHERE user_id = %s 
          AND user_id IS NOT NULL 
          AND user_id != '' 
          AND (is_guest = FALSE OR is_guest IS NULL)
        ORDER BY timestamp DESC
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def set_active_session(store_id, bay_id, user_id):
    """타석에 활성 사용자 등록 (active_sessions + bays 테이블 모두 업데이트)"""
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # 1. active_sessions 테이블에 등록
        cur.execute("""
            INSERT INTO active_sessions (store_id, bay_id, user_id, login_time)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (store_id, bay_id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                login_time = EXCLUDED.login_time
        """, (store_id, bay_id, user_id, now))
        
        # 2. bays 테이블에도 활성 사용자 등록 (샷 수집 프로그램이 조회할 수 있도록)
        cur.execute("""
            UPDATE bays 
            SET user_id = %s, last_update = %s
            WHERE store_id = %s AND bay_id = %s
        """, (user_id, now, store_id, bay_id))
        
        conn.commit()
        print(f"[DEBUG] 활성 사용자 등록: store_id={store_id}, bay_id={bay_id}, user_id={user_id}")
    except Exception as e:
        print(f"[ERROR] set_active_session 오류: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def clear_active_session(store_id, bay_id):
    """타석의 활성 사용자 제거 (active_sessions + bays 테이블 모두 업데이트)"""
    # store_id나 bay_id가 None이면 처리하지 않음
    if not store_id or not bay_id:
        print(f"[WARNING] clear_active_session: store_id 또는 bay_id가 None입니다. (store_id={store_id}, bay_id={bay_id})")
        return 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. active_sessions 테이블에서 제거
        cur.execute("""
            DELETE FROM active_sessions WHERE store_id = %s AND bay_id = %s
        """, (store_id, bay_id))
        deleted_count = cur.rowcount
        
        # 2. bays 테이블에서도 활성 사용자 제거 (NULL로 설정)
        cur.execute("""
            UPDATE bays 
            SET user_id = NULL, last_update = CURRENT_TIMESTAMP
            WHERE store_id = %s AND bay_id = %s
        """, (store_id, bay_id))
        
        conn.commit()
        return deleted_count
    except Exception as e:
        print(f"[ERROR] clear_active_session 오류: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return 0
    finally:
        cur.close()
        conn.close()

def get_active_user(store_id, bay_id):
    """타석의 활성 사용자 조회 (bays 테이블 우선, 없으면 active_sessions 확인)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. bays 테이블에서 조회 (샷 수집 프로그램이 조회하는 방식)
        cur.execute("""
            SELECT user_id, last_update as login_time 
            FROM bays 
            WHERE store_id = %s AND bay_id = %s AND user_id IS NOT NULL AND user_id != ''
        """, (store_id, bay_id))
        row = cur.fetchone()
        
        if row and row.get("user_id"):
            result = dict(row)
            cur.close()
            conn.close()
            return result
        
        # 2. bays 테이블에 없으면 active_sessions 테이블 확인 (하위 호환)
        cur.execute("""
            SELECT user_id, login_time FROM active_sessions WHERE store_id = %s AND bay_id = %s
        """, (store_id, bay_id))
        row = cur.fetchone()
        
        # active_sessions에 있으면 bays 테이블에도 동기화
        if row and row.get("user_id"):
            cur.execute("""
                UPDATE bays 
                SET user_id = %s, last_update = %s
                WHERE store_id = %s AND bay_id = %s
            """, (row["user_id"], row.get("login_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")), store_id, bay_id))
            conn.commit()
            return dict(row)
        
        return None
    except Exception as e:
        print(f"[ERROR] get_active_user 오류: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_bay_active_user_info(store_id, bay_id):
    return get_active_user(store_id, bay_id)

def cleanup_expired_active_users_by_last_shot(ttl_minutes=10):
    """만료된 active_user 자동 정리 (최근 샷 10분 기준) - heartbeat 제거"""
    """
    active_user는 최근 샷으로만 유지된다.
    최근 샷이 10분간 없으면 자동 로그아웃 처리된다.
    프로그램 생존 여부는 판단 기준이 아니다.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        from datetime import timedelta
        # TTL 시간 이전을 기준으로 최근 샷 확인
        ttl_time = datetime.now() - timedelta(minutes=ttl_minutes)
        ttl_time_str = ttl_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. shots 테이블에서 각 타석의 최근 샷 시간 확인
        # user_id가 있고 게스트가 아닌 최근 샷만 확인
        cur.execute("""
            SELECT store_id, bay_id, MAX(timestamp) as last_shot_time
            FROM shots
            WHERE user_id IS NOT NULL 
              AND user_id != '' 
              AND (is_guest = FALSE OR is_guest IS NULL)
              AND timestamp >= %s
            GROUP BY store_id, bay_id
        """, (ttl_time_str,))
        
        active_bays = {f"{row[0]}_{row[1]}": row[2] for row in cur.fetchall()}
        
        # 2. bays 테이블에서 active_user가 있는 타석 확인
        cur.execute("""
            SELECT store_id, bay_id, user_id
            FROM bays
            WHERE user_id IS NOT NULL AND user_id != ''
        """)
        
        bays_with_active_user = cur.fetchall()
        cleaned_count = 0
        
        for store_id, bay_id, user_id in bays_with_active_user:
            bay_key = f"{store_id}_{bay_id}"
            last_shot_time = active_bays.get(bay_key)
            
            # 최근 샷이 없거나 10분 이상 지났으면 해제
            if not last_shot_time or last_shot_time < ttl_time_str:
                # active_user 해제
                cur.execute("""
                    UPDATE bays 
                    SET user_id = '', last_update = CURRENT_TIMESTAMP
                    WHERE store_id = %s AND bay_id = %s
                """, (store_id, bay_id))
                
                # active_sessions도 제거
                cur.execute("""
                    DELETE FROM active_sessions 
                    WHERE store_id = %s AND bay_id = %s
                """, (store_id, bay_id))
                
                cleaned_count += 1
                print(f"[INFO] active_user 자동 해제: store_id={store_id}, bay_id={bay_id}, user_id={user_id} (최근 샷 없음 또는 {ttl_minutes}분 초과)")
        
        conn.commit()
        if cleaned_count > 0:
            print(f"[INFO] 만료된 active_user 정리 완료: {cleaned_count}개 (최근 샷 {ttl_minutes}분 기준)")
        return cleaned_count
    except Exception as e:
        print(f"[ERROR] cleanup_expired_active_users_by_last_shot 오류: {e}")
        conn.rollback()
        return 0
    finally:
        cur.close()
        conn.close()

def cleanup_expired_active_users(ttl_minutes=5):
    """만료된 active_user 자동 정리 (TTL 정책)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        from datetime import timedelta
        # TTL 시간 이전의 last_update를 가진 active_user 제거
        ttl_time = datetime.now() - timedelta(minutes=ttl_minutes)
        ttl_time_str = ttl_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. bays 테이블에서 만료된 active_user 제거
        cur.execute("""
            UPDATE bays 
            SET user_id = '', last_update = CURRENT_TIMESTAMP
            WHERE user_id IS NOT NULL 
              AND user_id != '' 
              AND last_update < %s
        """, (ttl_time_str,))
        bays_cleaned = cur.rowcount
        
        # 2. active_sessions 테이블에서도 만료된 세션 제거
        cur.execute("""
            DELETE FROM active_sessions 
            WHERE login_time < %s
        """, (ttl_time_str,))
        sessions_cleaned = cur.rowcount
        
        conn.commit()
        total_cleaned = bays_cleaned + sessions_cleaned
        if total_cleaned > 0:
            print(f"[INFO] 만료된 active_user 정리: {total_cleaned}개 (TTL: {ttl_minutes}분)")
        return total_cleaned
    except Exception as e:
        print(f"[ERROR] cleanup_expired_active_users 오류: {e}")
        conn.rollback()
        return 0
    finally:
        cur.close()
        conn.close()

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

def get_all_stores():
    """모든 매장 목록 조회"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM stores ORDER BY store_id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_bays(store_id):
    """매장의 승인된 타석 목록만 반환 (store_pcs를 기준으로 조회, bays가 없으면 자동 생성)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 매장 존재 여부만 확인 (bays_count 필터링 제거)
        cur.execute("SELECT store_id FROM stores WHERE store_id = %s", (store_id,))
        store = cur.fetchone()
        if not store:
            return []
        
        # 승인된 PC가 있는 타석만 조회 (store_pcs를 기준으로 LEFT JOIN)
        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d")
        
        # 디버그: 먼저 store_pcs의 전체 데이터 확인
        cur.execute("""
            SELECT store_id, store_name, bay_id, bay_name, status, usage_end_date
            FROM store_pcs 
            WHERE store_id = %s OR store_name IN (SELECT store_name FROM stores WHERE store_id = %s)
        """, (store_id, store_id))
        all_pcs = cur.fetchall()
        print(f"[DEBUG] get_bays 전체 store_pcs: store_id={store_id}, 총 {len(all_pcs)}개")
        for pc in all_pcs:
            print(f"[DEBUG] PC: store_id={pc.get('store_id')}, store_name={pc.get('store_name')}, bay_id={pc.get('bay_id')}, bay_name={pc.get('bay_name')}, status={pc.get('status')}, usage_end_date={pc.get('usage_end_date')}")
        
        # store_pcs를 기준으로 조회하고, bays가 없으면 생성
        # store_id 또는 store_name으로 조회 (PC 등록 시 store_name으로 저장될 수 있음)
        cur.execute("""
            SELECT DISTINCT 
                COALESCE(b.bay_id, sp.bay_id) as bay_id,
                COALESCE(sp.store_id, (SELECT store_id FROM stores WHERE store_name = sp.store_name LIMIT 1)) as store_id,
                COALESCE(b.status, 'READY') as status,
                COALESCE(b.user_id, '') as user_id,
                COALESCE(b.last_update, TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')) as last_update,
                COALESCE(b.bay_code, CONCAT(COALESCE(sp.store_id, (SELECT store_id FROM stores WHERE store_name = sp.store_name LIMIT 1)), '_', sp.bay_id)) as bay_code,
                sp.bay_name,
                sp.pc_name,
                sp.status as pc_status,
                sp.usage_end_date
            FROM store_pcs sp
            LEFT JOIN bays b ON (b.store_id = sp.store_id OR b.store_id = (SELECT store_id FROM stores WHERE store_name = sp.store_name LIMIT 1))
                                AND b.bay_id = sp.bay_id
            WHERE (sp.store_id = %s OR sp.store_name IN (SELECT store_name FROM stores WHERE store_id = %s))
              AND sp.status = 'active'
              AND sp.bay_id IS NOT NULL
              AND sp.bay_id != ''
              AND (sp.usage_end_date IS NULL OR sp.usage_end_date::date >= %s::date)
            ORDER BY bay_id
        """, (store_id, store_id, today_str))
        
        approved_bays = cur.fetchall()
        print(f"[DEBUG] get_bays 최종: store_id={store_id}, 조회된 타석 수={len(approved_bays)}")
        for bay in approved_bays:
            print(f"[DEBUG] 타석: bay_id={bay.get('bay_id')}, bay_name={bay.get('bay_name')}, pc_name={bay.get('pc_name')}, pc_status={bay.get('pc_status')}, usage_end_date={bay.get('usage_end_date')}")
        
        # bays 테이블에 없는 타석은 자동 생성
        for bay in approved_bays:
            bay_id_val = bay.get("bay_id")
            if bay_id_val:
                cur.execute("""
                    INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code)
                    VALUES (%s, %s, 'READY', NULL, CURRENT_TIMESTAMP, %s)
                    ON CONFLICT (store_id, bay_id) DO NOTHING
                """, (store_id, bay_id_val, f"{store_id}_{bay_id_val}"))
        
        if approved_bays:
            conn.commit()
        
        cur.close()
        conn.close()
        
        # 승인된 타석만 반환 (bays_count 필터링 제거 - 승인된 타석만 표시)
        # 모든 승인된 타석을 반환 (문자열 bay_id 포함)
        return [dict(bay) for bay in approved_bays]
        
    except Exception as e:
        print(f"[ERROR] get_bays 오류: {e}")
        import traceback
        traceback.print_exc()
        if cur:
            cur.close()
        if conn:
            conn.close()
        return []

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

# =========================
# 유저 대시보드 v3 (DRIVER 기준, is_valid=TRUE만)
# =========================

def get_today_summary_driver(user_id):
    """오늘 요약 데이터 (DRIVER, is_valid=TRUE만)"""
    from datetime import datetime
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    today = datetime.now().strftime("%Y-%m-%d")
    
    cur.execute("""
        SELECT 
            COUNT(*) as shot_count,
            AVG(carry) as avg_carry,
            AVG(total_distance) as avg_total_distance,
            AVG(smash_factor) as avg_smash_factor,
            AVG(ABS(face_angle)) as avg_face_angle,
            AVG(ABS(club_path)) as avg_club_path,
            AVG(ball_speed) as avg_ball_speed,
            AVG(club_speed) as avg_club_speed,
            AVG(back_spin) as avg_back_spin,
            AVG(ABS(side_spin)) as avg_side_spin
        FROM shots
        WHERE user_id = %s
          AND club_id = 'DRIVER'
          AND is_valid = TRUE
          AND is_guest = FALSE
          AND DATE(timestamp) = %s
    """, (user_id, today))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if row and row.get("shot_count", 0) > 0:
        return {
            "shot_count": int(row.get("shot_count", 0)),
            "avg_carry": round(float(row.get("avg_carry") or 0), 1),
            "avg_total_distance": round(float(row.get("avg_total_distance") or 0), 1),
            "avg_smash_factor": round(float(row.get("avg_smash_factor") or 0), 2),
            "avg_face_angle": round(float(row.get("avg_face_angle") or 0), 2),
            "avg_club_path": round(float(row.get("avg_club_path") or 0), 2),
            "avg_ball_speed": round(float(row.get("avg_ball_speed") or 0), 1),
            "avg_club_speed": round(float(row.get("avg_club_speed") or 0), 1),
            "avg_back_spin": round(float(row.get("avg_back_spin") or 0), 0),
            "avg_side_spin": round(float(row.get("avg_side_spin") or 0), 0)
        }
    return {
        "shot_count": 0,
        "avg_carry": 0.0,
        "avg_total_distance": 0.0,
        "avg_smash_factor": 0.0,
        "avg_face_angle": 0.0,
        "avg_club_path": 0.0,
        "avg_ball_speed": 0.0,
        "avg_club_speed": 0.0,
        "avg_back_spin": 0.0,
        "avg_side_spin": 0.0
    }

def get_recent_shots_driver(user_id, limit=20):
    """최근 샷 목록 (DRIVER, is_valid=TRUE만)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT 
            timestamp,
            carry,
            total_distance,
            smash_factor,
            face_angle,
            club_path,
            ball_speed,
            club_speed,
            back_spin,
            side_spin,
            launch_angle
        FROM shots
        WHERE user_id = %s
          AND club_id = 'DRIVER'
          AND is_valid = TRUE
          AND is_guest = FALSE
        ORDER BY timestamp DESC
        LIMIT %s
    """, (user_id, limit))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return [dict(row) for row in rows]

def get_7days_average_driver(user_id):
    """7일 평균 그래프 데이터 (DRIVER, is_valid=TRUE만)"""
    from datetime import datetime, timedelta
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 최근 7일 날짜 목록
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    
    results = []
    for date_str in dates:
        cur.execute("""
            SELECT 
                DATE(timestamp) as date,
                AVG(carry) as avg_carry,
                AVG(total_distance) as avg_total_distance,
                AVG(smash_factor) as avg_smash_factor,
                AVG(ABS(face_angle)) as avg_face_angle,
                AVG(ABS(club_path)) as avg_club_path,
                AVG(ball_speed) as avg_ball_speed,
                AVG(club_speed) as avg_club_speed,
                AVG(back_spin) as avg_back_spin,
                AVG(ABS(side_spin)) as avg_side_spin
            FROM shots
            WHERE user_id = %s
              AND club_id = 'DRIVER'
              AND is_valid = TRUE
              AND is_guest = FALSE
              AND DATE(timestamp) = %s
            GROUP BY DATE(timestamp)
        """, (user_id, date_str))
        
        row = cur.fetchone()
        if row:
            results.append({
                "date": row.get("date"),
                "avg_carry": round(float(row.get("avg_carry") or 0), 1),
                "avg_total_distance": round(float(row.get("avg_total_distance") or 0), 1),
                "avg_smash_factor": round(float(row.get("avg_smash_factor") or 0), 2),
                "avg_face_angle": round(float(row.get("avg_face_angle") or 0), 2),
                "avg_club_path": round(float(row.get("avg_club_path") or 0), 2),
                "avg_ball_speed": round(float(row.get("avg_ball_speed") or 0), 1),
                "avg_club_speed": round(float(row.get("avg_club_speed") or 0), 1),
                "avg_back_spin": round(float(row.get("avg_back_spin") or 0), 0),
                "avg_side_spin": round(float(row.get("avg_side_spin") or 0), 0)
            })
        else:
            results.append({
                "date": date_str,
                "avg_carry": 0.0,
                "avg_total_distance": 0.0,
                "avg_smash_factor": 0.0,
                "avg_face_angle": 0.0,
                "avg_club_path": 0.0,
                "avg_ball_speed": 0.0,
                "avg_club_speed": 0.0,
                "avg_back_spin": 0.0,
                "avg_side_spin": 0.0
            })
    
    cur.close()
    conn.close()
    return results

def get_criteria_compare_driver(user_id):
    """기준값 비교 데이터 (DRIVER, 최근 7일 평균 vs criteria.json)"""
    from datetime import datetime, timedelta
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 최근 7일 평균 계산
    cur.execute("""
        SELECT 
            AVG(carry) as avg_carry,
            AVG(total_distance) as avg_total_distance,
            AVG(smash_factor) as avg_smash_factor,
            AVG(ABS(face_angle)) as avg_face_angle,
            AVG(ABS(club_path)) as avg_club_path,
            AVG(ball_speed) as avg_ball_speed,
            AVG(club_speed) as avg_club_speed,
            AVG(back_spin) as avg_back_spin,
            AVG(ABS(side_spin)) as avg_side_spin
        FROM shots
        WHERE user_id = %s
          AND club_id = 'DRIVER'
          AND is_valid = TRUE
          AND is_guest = FALSE
          AND timestamp >= %s
    """, (user_id, (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row or not any(row.values()):
        return {}
    
    # 유저 성별 조회 (성별 없으면 male 기준)
    gender = None
    user = get_user(user_id)
    if user:
        gender = user.get("gender")
    
    # utils 모듈 import
    try:
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        user_dir = os.path.dirname(current_dir)
        if user_dir not in sys.path:
            sys.path.insert(0, user_dir)
        from utils import _get_rule, get_criteria_key
    except Exception as e:
        print(f"[WARNING] utils import 실패: {e}")
        return {}
    
    # criteria 키 결정 로그 (초기 점검용)
    club_id = "driver"
    criteria_key = get_criteria_key(club_id, gender)
    print(f"[CRITERIA] club={club_id}, gender={gender} → key={criteria_key}")
    
    # criteria.json 기준으로 비교 (성별 기준 적용)
    result = {}
    
    metrics_map = {
        "smash_factor": "smash_factor",
        "face_angle": "face_angle",
        "club_path": "club_path",
        "back_spin": "back_spin",
        "side_spin": "side_spin"
    }
    
    for metric_key, rule_key in metrics_map.items():
        avg_value = row.get(f"avg_{metric_key}")
        if avg_value is None:
            continue
        
        rule = _get_rule(club_id, rule_key, gender=gender)
        if not rule:
            continue
        
        good = rule.get("good")
        warn = rule.get("warn")
        bad = rule.get("bad")
        
        try:
            v = float(avg_value)
        except (ValueError, TypeError):
            continue
        
        # face_angle, club_path, side_spin은 절댓값 사용
        if metric_key in ["face_angle", "club_path", "side_spin"]:
            v = abs(v)
        
        # 기준 충족 여부 확인
        if isinstance(good, (list, tuple)) and len(good) == 2:
            low, high = float(good[0]), float(good[1])
            result[metric_key] = "GOOD" if (low <= v <= high) else "BAD"
        elif good is not None and bad is not None:
            g, b = float(good), float(bad)
            if v >= g:
                result[metric_key] = "GOOD"
            elif v <= b:
                result[metric_key] = "BAD"
            else:
                result[metric_key] = "WARN"
        elif good is not None and warn is not None:
            g, w = float(good), float(warn)
            if v <= g:
                result[metric_key] = "GOOD"
            elif v <= w:
                result[metric_key] = "WARN"
            else:
                result[metric_key] = "BAD"
        elif good is not None:
            g = float(good)
            result[metric_key] = "GOOD" if v >= g else "BAD"
    
    return result
