# ===== database.py (PostgreSQL) =====
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from urllib.parse import urlparse

# PostgreSQL 연결 정보 (Railway 환경 변수 또는 로컬 설정)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/golf_data")

def get_db_connection():
    """PostgreSQL 데이터베이스 연결"""
    try:
        # Railway의 DATABASE_URL 형식: postgresql://user:password@host:port/database
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")
        raise

# ------------------------------------------------
# DB 초기화 (❗ 기존 데이터 유지)
# ------------------------------------------------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1️⃣ 유저 테이블 (없으면 생성)
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
    
    # users 테이블에 name, phone 컬럼 추가 (없을 때만)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT")
    except Exception:
        pass
    
    try:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT")
    except Exception:
        pass

    # 2️⃣ 샷 테이블 (이미 있다면 그대로 사용)
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

    # 3️⃣ shots 테이블 컬럼 추가 (없을 때만)
    try:
        cur.execute("ALTER TABLE shots ADD COLUMN IF NOT EXISTS side_spin INTEGER")
    except Exception:
        pass

    try:
        cur.execute("ALTER TABLE shots ADD COLUMN IF NOT EXISTS back_spin INTEGER")
    except Exception:
        pass

    try:
        cur.execute("ALTER TABLE shots ADD COLUMN IF NOT EXISTS lateral_offset REAL")
    except Exception:
        pass

    try:
        cur.execute("ALTER TABLE shots ADD COLUMN IF NOT EXISTS direction_angle REAL")
    except Exception:
        pass

    try:
        cur.execute("ALTER TABLE shots ADD COLUMN IF NOT EXISTS total_distance REAL")
    except Exception:
        pass

    try:
        cur.execute("ALTER TABLE shots ADD COLUMN IF NOT EXISTS carry REAL")
    except Exception:
        pass

    # 4️⃣ 매장 / 타석 테이블 (관리자 화면용)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stores (
        store_id   TEXT PRIMARY KEY,
        store_name TEXT,
        admin_pw   TEXT,
        bays_count INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bays (
        store_id    TEXT,
        bay_id      TEXT,
        status      TEXT,
        user_id     TEXT,
        last_update TEXT,
        PRIMARY KEY (store_id, bay_id)
    )
    """)

    # 5️⃣ 활성 세션 테이블 (main.py에서 현재 로그인한 사용자 확인용)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS active_sessions (
        store_id    TEXT,
        bay_id      TEXT,
        user_id     TEXT,
        login_time  TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (store_id, bay_id)
    )
    """)

    # 기본 매장(gaja)이 없으면 생성 (타석은 매장 등록 시 생성되도록 함)
    cur.execute("SELECT COUNT(*) AS c FROM stores WHERE store_id = %s", ("gaja",))
    row = cur.fetchone()
    if not row or row[0] == 0:
        # 기본 매장만 생성 (타석은 매장 등록 시 생성되도록 함)
        cur.execute(
            "INSERT INTO stores (store_id, store_name, admin_pw, bays_count) VALUES (%s, %s, %s, %s)",
            ("gaja", "가자골프", "1111", 5),  # 기본값을 5개로 변경
        )
        # 기본 타석 생성 (5개)
        for i in range(1, 6):
            bay_id = f"{i:02d}"
            cur.execute(
                """
                INSERT INTO bays (store_id, bay_id, status, user_id, last_update)
                VALUES (%s, %s, 'READY', '', '')
                ON CONFLICT (store_id, bay_id) DO NOTHING
                """,
                ("gaja", bay_id),
            )
    else:
        # 기존 매장이 있으면 비밀번호를 1111로 업데이트 (기존 비밀번호가 다른 경우)
        cur.execute(
            "UPDATE stores SET admin_pw = %s WHERE store_id = %s",
            ("1111", "gaja")
        )
        # 기존 매장의 bays_count도 5로 업데이트 (10개로 설정된 경우)
        cur.execute(
            "UPDATE stores SET bays_count = %s WHERE store_id = %s AND bays_count > %s",
            (5, "gaja", 5)
        )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ DB 준비 완료 (기존 데이터 유지)")

# ------------------------------------------------
# 유저 관련
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
    cur.execute(
        "SELECT * FROM users WHERE user_id=%s",
        (user_id,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return dict(user) if user else None

def get_user_practice_dates(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT DISTINCT date(timestamp) AS d
        FROM shots
        WHERE user_id=%s
        ORDER BY d DESC
        """,
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

# ------------------------------------------------
# 샷 저장 (main.py와 연동)
# ------------------------------------------------
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

# ------------------------------------------------
# 유저 화면용 조회
# ------------------------------------------------
def get_practice_dates(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT DISTINCT date(timestamp) AS d
        FROM shots
        WHERE user_id=%s
        ORDER BY d DESC
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_shots_by_date(user_id, date_str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT *
        FROM shots
        WHERE user_id=%s AND date(timestamp)=%s
        ORDER BY timestamp ASC
    """, (user_id, date_str))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_last_shot(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT *
        FROM shots
        WHERE user_id=%s
        ORDER BY timestamp DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None

# ---------- 샷 리스트 ----------
def get_all_shots(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT *
        FROM shots
        WHERE user_id=%s
        ORDER BY timestamp DESC
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_shots_by_store(user_id, store_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT *
        FROM shots
        WHERE user_id=%s AND store_id=%s
        ORDER BY timestamp DESC
    """, (user_id, store_id))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_all_shots_by_store(store_id):
    """매장의 모든 샷 기록 가져오기 (관리자용)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT *
        FROM shots
        WHERE store_id=%s
        ORDER BY timestamp DESC
        LIMIT 100
    """, (store_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def get_shots_by_bay(store_id, bay_id):
    """특정 타석의 모든 샷 기록 가져오기 (관리자용)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT *
        FROM shots
        WHERE store_id=%s AND bay_id=%s
        ORDER BY timestamp DESC
        LIMIT 100
    """, (store_id, bay_id))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def check_user(user_id, password):
    """
    사용자 로그인 확인
    Returns: dict if user exists and password matches, None otherwise
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM users WHERE user_id=%s AND password=%s",
        (user_id, password)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    # Row 객체를 dict로 변환 (없으면 None)
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

def create_store(store_id, store_name, password, bays_count):
    """
    매장 등록
    기존 타석이 있으면 삭제하고 새로 생성
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 기존 타석 삭제 (있으면)
        cur.execute("DELETE FROM bays WHERE store_id = %s", (store_id,))
        
        # 매장 정보 저장 (기존 정보가 있으면 업데이트)
        cur.execute(
            """
            INSERT INTO stores (store_id, store_name, admin_pw, bays_count) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (store_id) DO UPDATE SET
                store_name = EXCLUDED.store_name,
                admin_pw = EXCLUDED.admin_pw,
                bays_count = EXCLUDED.bays_count
            """,
            (store_id, store_name, password, bays_count)
        )
        
        # 타석 생성
        for i in range(1, bays_count + 1):
            bay_id = f"{i:02d}"
            cur.execute(
                "INSERT INTO bays (store_id, bay_id, status, user_id, last_update) VALUES (%s, %s, 'READY', '', '')",
                (store_id, bay_id)
            )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    except Exception as e:
        print(f"매장 등록 오류: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# ------------------------------------------------
# 매장 / 타석 (관리자 화면용)
# ------------------------------------------------
def check_store(store_id, password):
    """
    관리자 로그인용 매장 계정 확인
    """
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
    """
    관리자 메인 화면에서 사용할 타석 목록
    stores 테이블의 bays_count를 기준으로 필터링
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 매장 정보 조회 (bays_count 확인)
    cur.execute(
        "SELECT bays_count FROM stores WHERE store_id = %s",
        (store_id,)
    )
    store = cur.fetchone()
    
    if not store:
        cur.close()
        conn.close()
        return []
    
    bays_count = store["bays_count"]
    
    # 모든 타석 조회 후 bays_count만큼만 필터링
    cur.execute(
        """
        SELECT *
        FROM bays
        WHERE store_id = %s
        ORDER BY bay_id
        """,
        (store_id,),
    )
    all_bays = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # bays_count만큼만 반환
    filtered_bays = []
    for bay in all_bays:
        bay_num = int(bay["bay_id"])
        if bay_num <= bays_count:
            filtered_bays.append(dict(bay))
    
    return filtered_bays

# ------------------------------------------------
# 활성 세션 관리 (main.py 연동)
# ------------------------------------------------
def set_active_session(store_id, bay_id, user_id):
    """
    로그인 시 활성 세션 등록
    """
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
    """
    로그아웃 시 활성 세션 삭제
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM active_sessions
        WHERE store_id = %s AND bay_id = %s
    """, (store_id, bay_id))
    conn.commit()
    deleted_count = cur.rowcount
    cur.close()
    conn.close()
    print(f"🗑️ 활성 세션 삭제: {store_id}/{bay_id} (삭제된 행: {deleted_count})")
    return deleted_count

def clear_all_active_sessions(store_id):
    """
    매장의 모든 활성 세션 삭제 (관리자용)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM active_sessions
        WHERE store_id = %s
    """, (store_id,))
    conn.commit()
    deleted_count = cur.rowcount
    cur.close()
    conn.close()
    print(f"🗑️ 모든 활성 세션 삭제: {store_id} (삭제된 행: {deleted_count})")
    return deleted_count

def get_active_user(store_id, bay_id):
    """
    main.py에서 현재 활성 사용자 조회
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT user_id, login_time
        FROM active_sessions
        WHERE store_id = %s AND bay_id = %s
    """, (store_id, bay_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None

def get_all_active_sessions(store_id):
    """
    매장의 모든 활성 세션 조회 (관리자 화면용)
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT store_id, bay_id, user_id, login_time
        FROM active_sessions
        WHERE store_id = %s
        ORDER BY bay_id
    """, (store_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

def is_bay_available(store_id, bay_id):
    """
    타석이 사용 가능한지 확인 (활성 세션이 없으면 True)
    """
    active = get_active_user(store_id, bay_id)
    return active is None

def get_bay_active_user_info(store_id, bay_id):
    """
    타석의 활성 사용자 정보 조회 (없으면 None)
    """
    return get_active_user(store_id, bay_id)
