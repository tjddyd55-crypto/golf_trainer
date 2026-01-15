from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import database
import socket
import json
import os
import importlib.util
import cv2
import numpy as np
import pytesseract
import re
from werkzeug.utils import secure_filename

def score_class(value, good, warn=None):
    """
    value : 숫자 or None
    good  : good 기준 (None 가능)
    warn  : warn 기준 (선택)

    반환: bg-good | bg-warn | bg-bad | bg-none
    """
    if value is None:
        return "bg-none"

    try:
        v = float(value)
    except:
        return "bg-none"

    # good이 None이면 bg-none 반환
    if good is None:
        return "bg-none"

    # good / bad만 있는 경우
    if warn is None:
        return "bg-good" if v >= good else "bg-bad"

    # good / warn / bad
    if v <= good:
        return "bg-good"
    elif v <= warn:
        return "bg-warn"
    else:
        return "bg-bad"


# =========================
# 기준값 로드 (config/criteria.json)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRITERIA_PATH = os.path.join(BASE_DIR, "config", "criteria.json")

try:
    with open(CRITERIA_PATH, "r", encoding="utf-8") as f:
        CRITERIA = json.load(f)
except Exception:
    CRITERIA = {}


def _get_rule(club_id, metric):
    """
    criteria.json 에서 클럽/지표별 기준값을 가져온다.
    - 우선순위: 해당 클럽 → "default"
    """
    cid = (club_id or "").lower()
    club_cfg = CRITERIA.get(cid, {})
    if metric in club_cfg:
        return club_cfg[metric]
    default_cfg = CRITERIA.get("default", {})
    return default_cfg.get(metric)


def classify_by_criteria(value, club_id, metric, *, fallback_good=None, fallback_warn=None, abs_value=False):
    """
    criteria.json 기반으로 색상 클래스 결정.
    - value: 실제 값
    - club_id: 클럽 ID (iron, driver 등)
    - metric: "smash_factor", "face_angle" 같은 이름
    - abs_value: True 이면 절대값 기준으로 판단
    - fallback_*: criteria 에서 못 찾았을 때 사용할 기존 기준값
    """
    if value is None:
        return "bg-none"

    try:
        v = float(value)
    except Exception:
        return "bg-none"

    if abs_value:
        v = abs(v)

    rule = _get_rule(club_id, metric)

    if rule:
        good = rule.get("good")
        warn = rule.get("warn")
        bad = rule.get("bad")

        # good 이 범위값([min,max])인 경우
        if isinstance(good, (list, tuple)) and len(good) == 2:
            low, high = float(good[0]), float(good[1])
            return "bg-good" if (low <= v <= high) else "bg-bad"

        # good / bad 모두 있는 경우: good 이상 / bad 이하 / 그 사이 warn
        if good is not None and bad is not None:
            g = float(good)
            b = float(bad)
            if v >= g:
                return "bg-good"
            if v <= b:
                return "bg-bad"
            return "bg-warn"

        # good / warn 만 있는 경우: 기존 score_class 와 동일 로직
        if good is not None and warn is not None:
            g = float(good)
            w = float(warn)
            if v <= g:
                return "bg-good"
            elif v <= w:
                return "bg-warn"
            else:
                return "bg-bad"

        # good 하나만 있는 경우: 기준 이상 good, 미만 bad
        if good is not None:
            g = float(good)
            return "bg-good" if v >= g else "bg-bad"

    # criteria 에 규칙이 없으면 기존 하드코딩 기준 사용
    # fallback_good이 None이면 bg-none 반환
    if fallback_good is None:
        return "bg-none"
    return score_class(v, fallback_good, fallback_warn)


app = Flask(__name__)
# 시크릿 키는 환경 변수에서 가져오거나 기본값 사용 (프로덕션에서는 반드시 환경 변수로 설정)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "golf_app_secret_key_change_in_production")

# =========================
# 서버 IP 표시용
# =========================
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# =========================
# DB 준비
# =========================
database.init_db()
print("✅ DB 준비 완료 (기존 데이터 유지)")

# =========================
# 메인
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# =========================
# 유저 회원가입
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        uid = request.form.get("user_id")
        pw = request.form.get("password")
        name = request.form.get("name")
        phone = request.form.get("phone")
        gender = request.form.get("gender")

        try:
            database.create_user(uid, pw, name, phone, gender)
            return redirect(url_for("login"))
        except:
            return "이미 존재하는 아이디입니다."

    return render_template("user_signup.html")

# =========================
# 유저 로그인
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid = request.form.get("user_id")
        pw = request.form.get("password")
        store_id = request.form.get("store_id", "gaja")
        bay_id = request.form.get("bay_id", "01")
        force_login = request.form.get("force_login", "false") == "true"  # 강제 로그인 옵션

        user = database.check_user(uid, pw)
        if not user:
            return "아이디 또는 비밀번호가 틀렸습니다."

        # 타석 사용 가능 여부 확인
        active_user = database.get_bay_active_user_info(store_id, bay_id)
        if active_user and active_user["user_id"] != uid:
            if not force_login:
                # 다른 사용자가 사용 중
                return f"""
                <script>
                    if(confirm('{bay_id}번 타석은 현재 {active_user["user_id"]}님이 사용 중입니다.\\n\\n강제로 로그인하시겠습니까? (기존 사용자의 세션이 종료됩니다)')) {{
                        var form = document.createElement('form');
                        form.method = 'POST';
                        form.innerHTML = `
                            <input type='hidden' name='user_id' value='{uid}'>
                            <input type='hidden' name='password' value='{pw}'>
                            <input type='hidden' name='store_id' value='{store_id}'>
                            <input type='hidden' name='bay_id' value='{bay_id}'>
                            <input type='hidden' name='force_login' value='true'>
                        `;
                        document.body.appendChild(form);
                        form.submit();
                    }} else {{
                        location.href='/login';
                    }}
                </script>
                """

        # 로그인 처리
        session["user_id"] = uid
        session["store_id"] = store_id
        session["bay_id"] = bay_id
        # 활성 세션 등록 (main.py에서 조회 가능하도록)
        database.set_active_session(store_id, bay_id, uid)
        return redirect(url_for("user_main"))

    # GET 요청 시 사용 가능한 타석 정보 전달
    store_id = request.args.get("store_id", "gaja")
    active_sessions = database.get_all_active_sessions(store_id)
    bays = database.get_bays(store_id)
    
    # 타석별 활성 사용자 정보 매핑
    bay_status = {}
    for active_session in active_sessions:
        bay_status[active_session["bay_id"]] = active_session["user_id"]
    
    return render_template("user_login.html", 
                         store_id=store_id,
                         bays=bays,
                         bay_status=bay_status)

# =========================
# 유저 메인
# =========================
@app.route("/user/main")
def user_main():
    if "user_id" not in session:
        return redirect(url_for("login"))

    uid = session["user_id"]

    user = database.get_user(uid)
    last_shot = database.get_last_shot(uid)
    dates = database.get_user_practice_dates(uid)

    return render_template(
        "user_main.html",
        user=user,
        last_shot=last_shot,
        dates=dates
    )

# =========================
# 🔥 유저 전체 샷 리스트
# =========================
@app.route("/user/shots")
def user_shots():
    if "user_id" not in session:
        return redirect(url_for("login"))

    uid = session["user_id"]
    rows = database.get_all_shots(uid)

    shots = []
    for r in rows:
        s = dict(r)  # Row → dict

        club_id = s.get("club_id") or ""

        # 기본 안전 처리
        bs = s.get("ball_speed")
        sf = s.get("smash_factor")
        fa = s.get("face_angle")
        cp = s.get("club_path")
        lo = s.get("lateral_offset")
        da = s.get("direction_angle")
        ss = s.get("side_spin")
        bk = s.get("back_spin")

        # 볼 스피드 / 스매시
        s["ball_speed_class"] = classify_by_criteria(bs, club_id, "ball_speed", fallback_good=60)
        s["smash_class"] = classify_by_criteria(sf, club_id, "smash_factor", fallback_good=1.45)

        # 각도/이격: 절대값 기준
        s["face_class"] = classify_by_criteria(fa, club_id, "face_angle", abs_value=True, fallback_good=2.0, fallback_warn=4.0)
        s["path_class"] = classify_by_criteria(cp, club_id, "club_path", abs_value=True, fallback_good=2.0, fallback_warn=4.0)
        s["lateral_class"] = classify_by_criteria(lo, club_id, "lateral_offset", abs_value=True, fallback_good=3.0, fallback_warn=6.0)
        s["direction_class"] = classify_by_criteria(da, club_id, "direction_angle", abs_value=True, fallback_good=3.0, fallback_warn=6.0)

        # 스핀: 절대값 기준
        s["side_spin_class"] = classify_by_criteria(ss, club_id, "side_spin", abs_value=True, fallback_good=300, fallback_warn=600)
        s["back_spin_class"] = classify_by_criteria(bk, club_id, "back_spin", abs_value=False, fallback_good=None)

        shots.append(s)

    return render_template(
        "shots_all.html",
        shots=shots,
        title="전체 샷 기록"
    )

# =========================
# 관리자 매장 등록
# =========================
@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        store_id = request.form.get("store_id", "").upper()  # 대문자 변환
        store_name = request.form.get("store_name")
        password = request.form.get("password")
        bays_count = int(request.form.get("bays_count", 1))
        birth_date = request.form.get("birth_date") or None
        business_number = request.form.get("business_number") or None
        phone = request.form.get("phone") or None

        if database.create_store(store_id, store_name, password, bays_count, birth_date, business_number, phone):
            return f"<script>alert('{store_name} 매장 등록 성공!'); location.href='/admin/login';</script>"
        else:
            return "이미 존재하는 매장 코드입니다."

    return render_template("admin_signup.html")

# =========================
# 관리자 로그인
# =========================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        sid = request.form.get("store_id")
        pw = request.form.get("password")

        store = database.check_store(sid, pw)
        if store:
            session["store_id"] = sid
            return redirect(url_for("admin_main"))
        else:
            # 로그인 실패 시 에러 메시지 표시
            return render_template("admin_login.html", error="매장 코드 또는 비밀번호가 올바르지 않습니다.")

    return render_template("admin_login.html")

# =========================
# 관리자 메인
# =========================
@app.route("/admin")
def admin_main():
    if "store_id" not in session:
        return redirect(url_for("admin_login"))

    sid = session["store_id"]
    bays = database.get_bays(sid)
    
    # 활성 세션 정보 가져오기
    active_sessions = database.get_all_active_sessions(sid)
    active_map = {s["bay_id"]: s for s in active_sessions}
    
    # 디버깅: 활성 세션 정보 출력
    print(f"🔍 [관리자 페이지] 활성 세션: {active_sessions}")
    
    # 타석 정보에 활성 사용자 정보 추가
    bays_with_status = []
    for bay in bays:
        bay_dict = dict(bay)
        if bay_dict["bay_id"] in active_map:
            bay_dict["active_user"] = active_map[bay_dict["bay_id"]]["user_id"]
            bay_dict["login_time"] = active_map[bay_dict["bay_id"]]["login_time"]
            print(f"   ✅ {bay_dict['bay_id']}번 타석: {bay_dict['active_user']} 로그인 중")
        else:
            bay_dict["active_user"] = None
            print(f"   ⚪ {bay_dict['bay_id']}번 타석: 비어있음")
        bays_with_status.append(bay_dict)
    
    # 매장의 모든 샷 기록 가져오기
    rows = database.get_all_shots_by_store(sid)
    shots = []
    for r in rows:
        s = dict(r)
        club_id = s.get("club_id") or ""
        
        # 기본 안전 처리
        bs = s.get("ball_speed")
        sf = s.get("smash_factor")
        fa = s.get("face_angle")
        cp = s.get("club_path")
        lo = s.get("lateral_offset")
        da = s.get("direction_angle")
        ss = s.get("side_spin")
        bk = s.get("back_spin")
        
        # 볼 스피드 / 스매시
        s["ball_speed_class"] = classify_by_criteria(bs, club_id, "ball_speed", fallback_good=60)
        s["smash_class"] = classify_by_criteria(sf, club_id, "smash_factor", fallback_good=1.45)
        
        # 각도/이격: 절대값 기준
        s["face_class"] = classify_by_criteria(fa, club_id, "face_angle", abs_value=True, fallback_good=2.0, fallback_warn=4.0)
        s["path_class"] = classify_by_criteria(cp, club_id, "club_path", abs_value=True, fallback_good=2.0, fallback_warn=4.0)
        s["lateral_class"] = classify_by_criteria(lo, club_id, "lateral_offset", abs_value=True, fallback_good=3.0, fallback_warn=6.0)
        s["direction_class"] = classify_by_criteria(da, club_id, "direction_angle", abs_value=True, fallback_good=3.0, fallback_warn=6.0)
        
        # 스핀: 절대값 기준
        s["side_spin_class"] = classify_by_criteria(ss, club_id, "side_spin", abs_value=True, fallback_good=300, fallback_warn=600)
        s["back_spin_class"] = classify_by_criteria(bk, club_id, "back_spin", abs_value=False, fallback_good=None)
        
        shots.append(s)

    # 랭킹 및 오늘 방문 손님 데이터 (임시로 빈 리스트)
    male_rank = []
    today_users = []
    
    return render_template(
        "admin.html",
        store_id=sid,
        bays=bays_with_status,
        shots=shots,
        server_ip=get_ip_address(),
        male_rank=male_rank,
        today_users=today_users
    )

# =========================
# 🔥 샷 데이터 저장 API
# =========================
@app.route("/api/save_shot", methods=["POST"])
def save_shot():
    data = request.json
    print("📥 서버 수신 데이터:", data)
    database.save_shot_to_db(data)
    return jsonify({"status": "ok"})

# =========================
# 로그아웃
# =========================
@app.route("/logout")
def logout():
    # 활성 세션 삭제
    store_id = session.get("store_id")
    bay_id = session.get("bay_id")
    user_id = session.get("user_id")
    
    print(f"🔓 [로그아웃 요청] 사용자: {user_id}, 매장: {store_id}, 타석: {bay_id}")
    
    if store_id and bay_id:
        # 삭제 전 확인
        before = database.get_active_user(store_id, bay_id)
        print(f"   삭제 전 활성 세션: {before}")
        
        database.clear_active_session(store_id, bay_id)
        
        # 삭제 후 확인
        after = database.get_active_user(store_id, bay_id)
        print(f"   삭제 후 활성 세션: {after}")
        
        if after:
            print(f"   ⚠️ 경고: 세션 삭제 후에도 활성 세션이 남아있음!")
        else:
            print(f"   ✅ 활성 세션 삭제 완료")
    
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin/logout")
def admin_logout():
    """관리자 로그아웃"""
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin/bay/<store_id>/<bay_id>")
def admin_bay_shots(store_id, bay_id):
    """특정 타석의 샷 기록 보기"""
    if "store_id" not in session or session["store_id"] != store_id:
        return redirect(url_for("admin_login"))
    
    # 활성 세션 정보 가져오기
    active_session = database.get_active_user(store_id, bay_id)
    
    # 해당 타석의 샷 기록 가져오기
    rows = database.get_shots_by_bay(store_id, bay_id)
    shots = []
    for r in rows:
        s = dict(r)
        club_id = s.get("club_id") or ""
        
        # 기본 안전 처리
        bs = s.get("ball_speed")
        sf = s.get("smash_factor")
        fa = s.get("face_angle")
        cp = s.get("club_path")
        lo = s.get("lateral_offset")
        da = s.get("direction_angle")
        ss = s.get("side_spin")
        bk = s.get("back_spin")
        
        # 볼 스피드 / 스매시
        s["ball_speed_class"] = classify_by_criteria(bs, club_id, "ball_speed", fallback_good=60)
        s["smash_class"] = classify_by_criteria(sf, club_id, "smash_factor", fallback_good=1.45)
        
        # 각도/이격: 절대값 기준
        s["face_class"] = classify_by_criteria(fa, club_id, "face_angle", abs_value=True, fallback_good=2.0, fallback_warn=4.0)
        s["path_class"] = classify_by_criteria(cp, club_id, "club_path", abs_value=True, fallback_good=2.0, fallback_warn=4.0)
        s["lateral_class"] = classify_by_criteria(lo, club_id, "lateral_offset", abs_value=True, fallback_good=3.0, fallback_warn=6.0)
        s["direction_class"] = classify_by_criteria(da, club_id, "direction_angle", abs_value=True, fallback_good=3.0, fallback_warn=6.0)
        
        # 스핀: 절대값 기준
        s["side_spin_class"] = classify_by_criteria(ss, club_id, "side_spin", abs_value=True, fallback_good=300, fallback_warn=600)
        s["back_spin_class"] = classify_by_criteria(bk, club_id, "back_spin", abs_value=False, fallback_good=None)
        
        shots.append(s)
    
    return render_template(
        "shots_all.html",
        shots=shots,
        title=f"{store_id} 매장 {bay_id}번 타석 샷 기록",
        active_user=active_session.get("user_id") if active_session else None,
        login_time=active_session.get("login_time") if active_session else None
    )

# =========================
# API: 현재 활성 사용자 조회 (main.py용)
# =========================
@app.route("/api/active_user", methods=["GET"])
def get_active_user():
    store_id = request.args.get("store_id", "gaja")
    bay_id = request.args.get("bay_id", "01")
    active = database.get_active_user(store_id, bay_id)
    return jsonify(active if active else {"user_id": None})

@app.route("/api/debug/active_sessions", methods=["GET"])
def debug_active_sessions():
    """활성 세션 디버깅용 API (관리자용)"""
    if "store_id" not in session:
        return jsonify({"error": "관리자 로그인 필요"}), 403
    
    store_id = request.args.get("store_id", session.get("store_id"))
    all_sessions = database.get_all_active_sessions(store_id)
    
    return jsonify({
        "store_id": store_id,
        "active_sessions": all_sessions,
        "count": len(all_sessions)
    })

@app.route("/api/clear_session", methods=["POST"])
def clear_session():
    """활성 세션 강제 삭제 API (관리자용)"""
    if "store_id" not in session:
        return jsonify({"error": "관리자 로그인 필요"}), 403
    
    store_id = request.args.get("store_id")
    bay_id = request.args.get("bay_id")
    
    if not store_id or not bay_id:
        return jsonify({"error": "store_id와 bay_id가 필요합니다"}), 400
    
    # 삭제 전 확인
    before = database.get_active_user(store_id, bay_id)
    print(f"🔧 [세션 강제 삭제] 매장: {store_id}, 타석: {bay_id}")
    print(f"   삭제 전: {before}")
    
    # 세션 삭제
    deleted_count = database.clear_active_session(store_id, bay_id)
    
    # 삭제 후 확인
    after = database.get_active_user(store_id, bay_id)
    print(f"   삭제 후: {after}")
    
    if after:
        return jsonify({"status": "error", "error": "세션 삭제 실패"}), 500
    
    return jsonify({"status": "success", "message": "세션이 삭제되었습니다", "deleted_count": deleted_count})

@app.route("/api/clear_all_sessions", methods=["POST"])
def clear_all_sessions():
    """모든 활성 세션 강제 삭제 API (관리자용)"""
    if "store_id" not in session:
        return jsonify({"error": "관리자 로그인 필요"}), 403
    
    store_id = request.args.get("store_id", session.get("store_id"))
    
    # 삭제 전 확인
    before = database.get_all_active_sessions(store_id)
    print(f"🔧 [모든 세션 강제 삭제] 매장: {store_id}")
    print(f"   삭제 전 활성 세션: {before}")
    
    # 모든 세션 삭제
    deleted_count = database.clear_all_active_sessions(store_id)
    
    # 삭제 후 확인
    after = database.get_all_active_sessions(store_id)
    print(f"   삭제 후 활성 세션: {after}")
    
    return jsonify({
        "status": "success", 
        "message": f"모든 세션이 삭제되었습니다",
        "deleted_count": deleted_count
    })

# =========================
# 드라이버샷 화면 캡처 테스트
# =========================
@app.route("/test/capture")
def test_capture():
    """
    화면 캡처 테스트 페이지
    """
    return render_template("test_capture.html")

# =========================
# API: 영역 정보 조회
# =========================
@app.route("/api/regions", methods=["GET"])
def get_regions():
    try:
        regions_path = os.path.join(BASE_DIR, "regions", "test.json")
        with open(regions_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# API: 샷 데이터 읽기 테스트
# =========================
@app.route("/api/test_read_shot", methods=["POST"])
def test_read_shot():
    """
    main.py의 read_metrics 함수를 직접 호출하여 테스트
    """
    try:
        # main.py의 함수들을 임포트하여 사용
        main_path = os.path.join(BASE_DIR, "main.py")
        spec = importlib.util.spec_from_file_location("main_module", main_path)
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        # read_metrics 함수 호출
        metrics = main_module.read_metrics()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": f"테스트 실패: {str(e)}. main.py가 정상적으로 로드되지 않았습니다."}), 500

# =========================
# API: 업로드된 이미지에서 OCR 테스트
# =========================
@app.route("/api/test_upload_image", methods=["POST"])
def test_upload_image():
    """
    업로드된 캡처 이미지에서 OCR로 샷 데이터 읽기
    """
    try:
        if 'image' not in request.files:
            return jsonify({"error": "이미지 파일이 없습니다."}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "파일이 선택되지 않았습니다."}), 400
        
        # 이미지 읽기
        file_bytes = file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        full_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if full_image is None:
            return jsonify({"error": "이미지를 읽을 수 없습니다."}), 400
        
        # regions 파일 로드
        regions_path = os.path.join(BASE_DIR, "regions", "test.json")
        with open(regions_path, "r", encoding="utf-8") as f:
            regions_data = json.load(f)
        
        regions = regions_data["regions"]
        img_h, img_w = full_image.shape[:2]
        
        # OCR 함수들 (main.py와 동일한 로직)
        def preprocess(img):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
            gray = cv2.GaussianBlur(gray, (3,3), 0)
            gray = cv2.threshold(gray, 145, 255, cv2.THRESH_BINARY)[1]
            return gray
        
        def ocr_text_region(key):
            """영역을 추출하여 OCR 수행 (개선된 전처리)"""
            try:
                region = regions[key]
                x = int(region["x"] * img_w)
                y = int(region["y"] * img_h)
                w = int(region["w"] * img_w)
                h = int(region["h"] * img_h)
                
                # 영역이 이미지 범위를 벗어나지 않도록 체크
                x = max(0, min(x, img_w - 1))
                y = max(0, min(y, img_h - 1))
                w = min(w, img_w - x)
                h = min(h, img_h - y)
                
                if w <= 0 or h <= 0:
                    return ""
            except Exception:
                return ""
            
            # 영역 추출
            roi = full_image[y:y+h, x:x+w]
            
            # 백스핀과 사이드스핀은 더 크게 확대
            if key == "back_spin":
                # 백스핀: 최소 250px 너비로 확대하여 4자리 숫자 전체 인식
                if w < 250 or h < 70:
                    scale = max(7.0, 250.0 / w, 70.0 / h)
                    roi = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            elif key == "side_spin":
                # 사이드 스핀: 최소 250px 너비로 확대하여 3자리 숫자 전체 인식
                if w < 250 or h < 70:
                    scale = max(7.0, 250.0 / w, 70.0 / h)
                    roi = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            else:
                if w < 100 or h < 40:
                    scale = max(4.0, 100.0 / w, 40.0 / h)
                    roi = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            
            # 전처리
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 방법 1: 정규화 + 블러 + 일반 threshold (가장 빠르고 효과적)
            gray1 = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
            gray1 = cv2.GaussianBlur(gray1, (3, 3), 0)
            
            # 백스핀과 사이드스핀은 더 많은 threshold 값 시도
            if key in ["back_spin", "side_spin"]:
                priority_combinations = [
                    (gray1, 145, 8),  # PSM 8 (단일 단어) 우선 시도
                    (gray1, 150, 8),
                    (gray1, 140, 8),
                    (gray1, 145, 7),
                    (gray1, 150, 7),
                    (gray1, 140, 7),
                    (gray1, 135, 7),  # 스핀 항목 추가
                    (gray1, 155, 7),  # 스핀 항목 추가
                    (gray1, 145, 6),  # PSM 6도 시도
                ]
                # CLAHE 적용 (대비 강화)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)
                gray1 = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
                gray1 = cv2.GaussianBlur(gray1, (3, 3), 0)
            else:
                priority_combinations = [
                    (gray1, 145, 7),  # 가장 일반적인 조합
                    (gray1, 150, 7),
                    (gray1, 140, 7),
                    (gray1, 145, 8),  # PSM 8도 시도
                ]
            
            best_text = None
            best_digits = 0
            
            for processed, thresh_val, psm_mode in priority_combinations:
                try:
                    thresh = cv2.threshold(processed, thresh_val, 255, cv2.THRESH_BINARY)[1]
                    text = pytesseract.image_to_string(
                        thresh,
                        lang="eng",
                        config=f"--psm {psm_mode} -c tessedit_char_whitelist=0123456789.,-RL /mps°",
                        timeout=1  # timeout 단축
                    ).upper().strip()
                    if text and any(c.isdigit() for c in text):
                        digits = sum(c.isdigit() for c in text)
                        
                        # 백스핀: 4자리 숫자 우선
                        if key == "back_spin":
                            # 가장 많은 숫자를 가진 결과 선택
                            if digits > best_digits:
                                best_text = text
                                best_digits = digits
                            # 4자리면 즉시 반환
                            if digits >= 4:
                                return text
                        # 사이드 스핀: 3자리 숫자 우선
                        elif key == "side_spin":
                            # 정확히 3자리면 즉시 반환
                            if digits == 3:
                                return text
                            # 가장 많은 숫자를 가진 결과 선택
                            if digits > best_digits:
                                best_text = text
                                best_digits = digits
                        else:
                            return text  # 즉시 반환 (조기 종료)
                except Exception:
                    continue
            
            # 백스핀: 최선의 결과 반환 (4자리 못 찾았어도)
            if key == "back_spin" and best_text:
                return best_text
            # 사이드 스핀: 최선의 결과 반환 (3자리 못 찾았어도)
            if key == "side_spin" and best_text:
                return best_text
            
            # 실패 시 적응형 threshold 시도 (1회만)
            try:
                gray2 = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY_INV, 11, 2
                )
                text = pytesseract.image_to_string(
                    gray2,
                    lang="eng",
                    config="--psm 7 -c tessedit_char_whitelist=0123456789.,-RL /mps°",
                    timeout=1
                ).upper().strip()
                if text and any(c.isdigit() for c in text):
                    if key == "back_spin":
                        digits = sum(c.isdigit() for c in text)
                        if digits >= 3:
                            return text
                    elif key == "side_spin":
                        digits = sum(c.isdigit() for c in text)
                        if digits >= 2:  # 사이드 스핀은 3자리지만 2자리 이상이면 일단 반환
                            return text
                    else:
                        return text
            except Exception:
                pass
            
            # 마지막 시도: whitelist 없이
            try:
                thresh = cv2.threshold(gray1, 145, 255, cv2.THRESH_BINARY)[1]
                text = pytesseract.image_to_string(
                    thresh,
                    lang="eng",
                    config="--psm 7",
                    timeout=1
                ).upper().strip()
                return text
            except Exception:
                return ""
        
        def parse_value(text, mode="plain", key=None):
            """
            main.py와 동일한 로직으로 개선된 파싱 함수
            백스핀: 4자리 숫자 우선
            사이드 스핀: 3자리 숫자 우선 (부호 포함)
            """
            if not text:
                return None
            
            # OCR 결과에서 불필요한 문자 제거 (뒤에 붙은 '-' 등)
            text_clean = text.strip()
            
            # 연속된 '-' 정리 (맨 앞의 '-'만 유지)
            if text_clean.startswith("-"):
                text_clean = "-" + text_clean[1:].replace("-", "")
            else:
                text_clean = text_clean.replace("-", "")
            
            # 백스핀: 정확히 4자리 숫자를 우선적으로 찾기
            if key == "back_spin":
                # 모든 숫자 추출 (순서대로)
                all_digits = re.findall(r'\d', text_clean)
                
                if len(all_digits) >= 4:
                    # 앞의 4자리 숫자만 사용
                    num_str = ''.join(all_digits[:4])
                    try:
                        v = float(num_str)
                        return abs(v)  # 백스핀은 부호 없음
                    except ValueError:
                        pass
                
                # 정규표현식으로도 시도
                m = re.search(r"\d{4}(?!\d)", text_clean)  # 4자리 숫자 뒤에 숫자가 없는 경우
                if m:
                    num_str = m.group(0).replace(",", "")
                    try:
                        v = float(num_str)
                        return abs(v)
                    except ValueError:
                        pass
                
                # 4자리 숫자 뒤에 숫자가 있어도 앞의 4자리만 추출
                m = re.search(r"(\d{4})\d+", text_clean)
                if m:
                    num_str = m.group(1)
                    try:
                        v = float(num_str)
                        return abs(v)
                    except ValueError:
                        pass
            
            # 사이드 스핀: 3자리 또는 4자리 숫자 처리 (부호 포함)
            if key == "side_spin":
                # 원본 텍스트에서 부호 확인 (OCR 오류로 인한 잘못된 부호 제거)
                original_text = text.strip()
                has_minus_sign = False
                
                # 명확한 부호 확인: 텍스트 시작 부분에 "-"가 있고, 그 뒤에 숫자가 오는 경우만
                if original_text.startswith("-") and len(original_text) > 1 and original_text[1].isdigit():
                    has_minus_sign = True
                
                # 모든 숫자 추출 (순서대로)
                all_digits = re.findall(r'\d', text_clean)
                
                # 4자리 숫자 우선 처리 (-1070 같은 경우)
                if len(all_digits) >= 4:
                    # 앞의 4자리 숫자 사용
                    # 예: "10706" → "1070", "1070" → "1070"
                    num_str = ''.join(all_digits[:4])
                    try:
                        v = float(num_str)
                        if mode == "minus":
                            # 명확한 부호가 있을 때만 음수로 처리
                            if has_minus_sign:
                                return -abs(v)
                            return abs(v)
                        return abs(v)
                    except ValueError:
                        pass
                
                # 3자리 숫자 처리 (655 같은 경우)
                if len(all_digits) >= 3:
                    # 앞의 3자리 숫자만 사용
                    # 예: "6556" → "655", "655" → "655"
                    num_str = ''.join(all_digits[:3])
                    try:
                        v = float(num_str)
                        if mode == "minus":
                            # 명확한 부호가 있을 때만 음수로 처리
                            if has_minus_sign:
                                return -abs(v)
                            return abs(v)
                        return abs(v)
                    except ValueError:
                        pass
                
                # 정규표현식으로도 시도: 4자리 숫자 우선, 그 다음 3자리
                m = re.search(r"\d{4}(?!\d)", text_clean)  # 4자리 숫자 뒤에 숫자가 없는 경우 (부호 제외)
                if m:
                    num_str = m.group(0).replace(",", "")
                    try:
                        v = float(num_str)
                        if mode == "minus":
                            if has_minus_sign:
                                return -abs(v)
                            return abs(v)
                        return abs(v)
                    except ValueError:
                        pass
                
                m = re.search(r"\d{3}(?!\d)", text_clean)  # 3자리 숫자 뒤에 숫자가 없는 경우 (부호 제외)
                if m:
                    num_str = m.group(0).replace(",", "")
                    try:
                        v = float(num_str)
                        if mode == "minus":
                            if has_minus_sign:
                                return -abs(v)
                            return abs(v)
                        return abs(v)
                    except ValueError:
                        pass
                
                # 4자리 이상 숫자 뒤에 숫자가 있어도 앞의 4자리만 추출 (10706 → 1070)
                m = re.search(r"(\d{4})\d+", text_clean)  # 부호 제외하고 숫자만
                if m:
                    num_str = m.group(1)
                    try:
                        v = float(num_str)
                        if mode == "minus":
                            if has_minus_sign:
                                return -abs(v)
                            return abs(v)
                        return abs(v)
                    except ValueError:
                        pass
                
                # 3자리 숫자 뒤에 숫자가 있어도 앞의 3자리만 추출 (6556 → 655)
                m = re.search(r"(\d{3})\d+", text_clean)  # 부호 제외하고 숫자만
                if m:
                    num_str = m.group(1)
                    try:
                        v = float(num_str)
                        if mode == "minus":
                            if has_minus_sign:
                                return -abs(v)
                            return abs(v)
                        return abs(v)
                    except ValueError:
                        pass
            
            # 일반 숫자 추출 (백스핀/사이드스핀이 아닌 경우)
            # 소수점이 있는 숫자를 우선적으로 찾기 (볼스피드/클럽스피드/클럽패스 등)
            # 소수점 인식 강화: 소수점 앞뒤로 숫자가 있는 패턴 우선
            m = re.search(r"-?\d+\.\d+", text_clean)
            if not m:
                # 소수점이 없으면 정수만 찾기
                # 먼저 쉼표 포함 숫자 시도
                m = re.search(r"-?\d{1,3}(?:,\d{3})+", text_clean)
            if not m:
                # 정확히 4자리 숫자 우선 시도 (백스핀용)
                m = re.search(r"-?\d{4}", text_clean)
            if not m:
                # 쉼표 없는 4자리 이상 숫자 시도
                m = re.search(r"-?\d{4,}", text_clean)
            if not m:
                # 일반 숫자 (1자리 이상)
                m = re.search(r"-?\d+", text_clean)
            if not m:
                return None
            
            # 쉼표 제거 후 숫자 변환
            num_str = m.group(0).replace(",", "")
            try:
                v = float(num_str)
            except ValueError:
                return None
            
            if mode == "plain":
                # 부호 없는 순수 숫자 (볼스피드, 클럽스피드 등)
                # 단, 소수점이 있는 경우 원래 값 유지 (음수면 음수, 양수면 양수)
                # 볼스피드/클럽스피드는 항상 양수이므로 abs 사용
                return abs(v)
            elif mode == "minus":
                # '-' 기호가 있으면 음수, 없으면 양수
                # 예: "-866 rpm" → -866, "989 rpm" → 989, "-4.7" → -4.7, "4.7" → 4.7
                # 원본 text에서 명확한 부호 확인 (텍스트 시작 부분에 "-"가 있고 그 뒤에 숫자가 오는 경우만)
                original_text = text.strip()
                has_minus_sign = False
                if original_text.startswith("-") and len(original_text) > 1:
                    # "-" 뒤에 숫자나 소수점이 오는 경우만 부호로 인정
                    next_char = original_text[1]
                    if next_char.isdigit() or next_char == ".":
                        has_minus_sign = True
                
                if has_minus_sign or num_str.startswith("-"):
                    return -abs(v)
                return abs(v)
            elif mode == "RL":
                text_upper = text.upper()
                if "L" in text_upper:
                    return -abs(v)
                if "R" in text_upper:
                    return abs(v)
                return v
            return v
        
        # 모든 영역 읽기
        bs_txt = ocr_text_region("ball_speed")
        cs_txt = ocr_text_region("club_speed")
        la_txt = ocr_text_region("launch_angle")
        bk_txt = ocr_text_region("back_spin")
        cp_txt = ocr_text_region("club_path")
        lo_txt = ocr_text_region("lateral_offset")
        da_txt = ocr_text_region("direction_angle")
        ss_txt = ocr_text_region("side_spin")
        fa_txt = ocr_text_region("face_angle")
        
        # 파싱
        ball_speed = parse_value(bs_txt, mode="plain")
        club_speed = parse_value(cs_txt, mode="plain")
        launch_angle = parse_value(la_txt, mode="plain")
        back_spin = parse_value(bk_txt, mode="plain", key="back_spin")
        side_spin = parse_value(ss_txt, mode="minus", key="side_spin")
        club_path = parse_value(cp_txt, mode="minus")
        lateral = parse_value(lo_txt, mode="RL")
        direction = parse_value(da_txt, mode="RL")
        face_angle = parse_value(fa_txt, mode="RL")
        
        # 스매시 팩터 계산
        smash_factor = None
        if ball_speed is not None and club_speed not in (None, 0, 0.0):
            try:
                smash_factor = round(ball_speed / club_speed, 2)
            except:
                smash_factor = None
        
        metrics = {
            "ball_speed": ball_speed,
            "club_speed": club_speed,
            "launch_angle": launch_angle,
            "back_spin": back_spin,
            "club_path": club_path,
            "lateral_offset": lateral,
            "direction_angle": direction,
            "side_spin": side_spin,
            "face_angle": face_angle,
            "smash_factor": smash_factor,
        }
        
        # 원본 OCR 텍스트도 함께 반환
        ocr_texts = {
            "ball_speed": bs_txt,
            "club_speed": cs_txt,
            "launch_angle": la_txt,
            "back_spin": bk_txt,
            "club_path": cp_txt,
            "lateral_offset": lo_txt,
            "direction_angle": da_txt,
            "side_spin": ss_txt,
            "face_angle": fa_txt,
        }
        
        # 디버깅: 각 영역의 이미지 정보도 포함 (선택적)
        # regions.json의 순서대로 정렬
        debug_info = {}
        if request.args.get("debug") == "true":
            import base64
            from io import BytesIO
            from collections import OrderedDict
            
            # regions.json의 키 순서 유지
            region_keys = list(regions.keys())
            
            for key in region_keys:
                try:
                    region = regions[key]
                    x = int(region["x"] * img_w)
                    y = int(region["y"] * img_h)
                    w = int(region["w"] * img_w)
                    h = int(region["h"] * img_h)
                    
                    # 영역이 이미지 범위를 벗어나지 않도록 체크
                    x = max(0, min(x, img_w - 1))
                    y = max(0, min(y, img_h - 1))
                    w = min(w, img_w - x)
                    h = min(h, img_h - y)
                    
                    if w > 0 and h > 0:
                        roi = full_image[y:y+h, x:x+w]
                        # 이미지 인코딩
                        _, buffer = cv2.imencode('.png', roi)
                        img_base64 = base64.b64encode(buffer).decode('utf-8')
                        debug_info[key] = {
                            "region": {"x": x, "y": y, "w": w, "h": h},
                            "image": f"data:image/png;base64,{img_base64}"
                        }
                except Exception as e:
                    debug_info[key] = {
                        "error": str(e),
                        "region": {"x": x if 'x' in locals() else 0, "y": y if 'y' in locals() else 0, "w": w if 'w' in locals() else 0, "h": h if 'h' in locals() else 0}
                    }
        
        result = {
            "metrics": metrics,
            "ocr_texts": ocr_texts,
            "image_size": {"width": img_w, "height": img_h}
        }
        
        if debug_info:
            result["debug_regions"] = debug_info
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        return jsonify({"error": f"처리 중 오류 발생: {str(e)}\n{traceback.format_exc()}"}), 500

# =========================
# API: main.py 상태 확인
# =========================
@app.route("/api/main_status", methods=["GET"])
def get_main_status():
    """
    main.py 실행 상태 확인 (간접적으로)
    """
    try:
        # 활성 사용자 조회로 간접 확인
        active = database.get_active_user("gaja", "01")
        return jsonify({
            "status": "ok",
            "active_user": active.get("user_id") if active else None,
            "message": "main.py가 실행 중이면 활성 사용자 정보를 조회할 수 있습니다."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# 서버 실행
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    print(f"🚀 서버 시작: http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)