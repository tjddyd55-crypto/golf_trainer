# ===== services/store_admin/app.py (매장 관리자 서비스) =====
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sys
import os

# 공유 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
local_shared = os.path.join(current_dir, 'shared')
if os.path.exists(local_shared):
    sys.path.insert(0, current_dir)
else:
    project_root = os.path.abspath(os.path.join(current_dir, '../../'))
    sys.path.insert(0, project_root)
from shared import database
from shared.auth import require_role

app = Flask(__name__, 
            template_folder='templates',
            static_folder='../../static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "golf_app_secret_key_change_in_production")

# 데이터베이스 초기화
database.init_db()

# =========================
# 매장 관리자 회원가입
# =========================
@app.route("/signup", methods=["GET", "POST"])
def store_admin_signup():
    if request.method == "POST":
        store_id = request.form.get("store_id")
        store_name = request.form.get("store_name")
        password = request.form.get("password")
        bays_count = int(request.form.get("bays_count", 5))

        if database.create_store(store_id, store_name, password, bays_count):
            return redirect(url_for("store_admin_login"))
        else:
            return "매장 등록 실패"

    return render_template("store_admin_signup.html")

# =========================
# 매장 관리자 로그인
# =========================
@app.route("/login", methods=["GET", "POST"])
def store_admin_login():
    if request.method == "POST":
        store_id = request.form.get("store_id")
        password = request.form.get("password")

        store = database.check_store(store_id, password)
        if not store:
            return render_template("store_admin_login.html", error="매장 코드 또는 비밀번호가 틀렸습니다.")

        # 세션 설정
        session["store_id"] = store_id
        session["role"] = "store_admin"
        return redirect(url_for("store_admin_dashboard"))

    return render_template("store_admin_login.html")

# =========================
# 매장 관리자 대시보드
# =========================
@app.route("/")
@require_role("store_admin")
def store_admin_dashboard():
    from .utils import classify_by_criteria
    
    store_id = session.get("store_id")
    bays = database.get_bays(store_id)
    active_sessions = database.get_all_active_sessions(store_id)
    rows = database.get_all_shots_by_store(store_id)
    
    # 샷 데이터에 색상 클래스 추가
    shots = []
    for r in rows[:20]:  # 최근 20개만
        s = dict(r)
        club_id = s.get("club_id") or ""
        bs = s.get("ball_speed")
        sf = s.get("smash_factor")
        s["ball_speed_class"] = classify_by_criteria(bs, club_id, "ball_speed", fallback_good=60)
        s["smash_class"] = classify_by_criteria(sf, club_id, "smash_factor", fallback_good=1.45)
        shots.append(s)

    # 타석별 활성 사용자 매핑
    bay_active_users = {}
    for session_info in active_sessions:
        key = f"{session_info['store_id']}_{session_info['bay_id']}"
        bay_active_users[key] = session_info

    return render_template("store_admin_dashboard.html",
                         store_id=store_id,
                         bays=bays,
                         active_sessions=active_sessions,
                         bay_active_users=bay_active_users,
                         shots=shots)

# =========================
# 타석별 샷 기록
# =========================
@app.route("/bay/<store_id>/<bay_id>")
@require_role("store_admin")
def bay_shots(store_id, bay_id):
    from .utils import classify_by_criteria
    
    rows = database.get_shots_by_bay(store_id, bay_id)
    shots = []
    for r in rows:
        s = dict(r)
        club_id = s.get("club_id") or ""
        
        # 색상 클래스 추가
        bs = s.get("ball_speed")
        sf = s.get("smash_factor")
        fa = s.get("face_angle")
        cp = s.get("club_path")
        lo = s.get("lateral_offset")
        da = s.get("direction_angle")
        ss = s.get("side_spin")
        bk = s.get("back_spin")
        
        s["ball_speed_class"] = classify_by_criteria(bs, club_id, "ball_speed", fallback_good=60)
        s["smash_class"] = classify_by_criteria(sf, club_id, "smash_factor", fallback_good=1.45)
        s["face_class"] = classify_by_criteria(fa, club_id, "face_angle", abs_value=True, fallback_good=2.0, fallback_warn=4.0)
        s["path_class"] = classify_by_criteria(cp, club_id, "club_path", abs_value=True, fallback_good=2.0, fallback_warn=4.0)
        s["lateral_class"] = classify_by_criteria(lo, club_id, "lateral_offset", abs_value=True, fallback_good=3.0, fallback_warn=6.0)
        s["direction_class"] = classify_by_criteria(da, club_id, "direction_angle", abs_value=True, fallback_good=3.0, fallback_warn=6.0)
        s["side_spin_class"] = classify_by_criteria(ss, club_id, "side_spin", abs_value=True, fallback_good=300, fallback_warn=600)
        s["back_spin_class"] = classify_by_criteria(bk, club_id, "back_spin", abs_value=False, fallback_good=None)
        
        shots.append(s)
    
    return render_template("bay_shots.html", 
                         store_id=store_id,
                         bay_id=bay_id,
                         shots=shots)

# =========================
# 세션 삭제
# =========================
@app.route("/api/clear_session", methods=["POST"])
@require_role("store_admin")
def clear_session():
    data = request.get_json()
    store_id = data.get("store_id")
    bay_id = data.get("bay_id")
    
    if store_id and bay_id:
        deleted = database.clear_active_session(store_id, bay_id)
        return jsonify({"success": True, "deleted": deleted})
    return jsonify({"success": False})

# =========================
# 모든 세션 삭제
# =========================
@app.route("/api/clear_all_sessions", methods=["POST"])
@require_role("store_admin")
def clear_all_sessions():
    store_id = session.get("store_id")
    deleted = database.clear_all_active_sessions(store_id)
    return jsonify({"success": True, "deleted": deleted})

# =========================
# 로그아웃
# =========================
@app.route("/pcs")
@require_role("store_admin")
def manage_pcs():
    """매장 PC 관리"""
    store_id = session.get("store_id")
    
    # 매장 이름 조회
    from psycopg2.extras import RealDictCursor
    conn = database.get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT store_name FROM stores WHERE store_id = %s", (store_id,))
    store = cur.fetchone()
    cur.close()
    conn.close()
    
    store_name = store["store_name"] if store else store_id
    
    # 해당 매장의 PC 목록 조회
    pcs = database.get_store_pcs_by_store(store_name)
    
    return render_template("manage_pcs.html",
                         store_id=store_id,
                         store_name=store_name,
                         pcs=pcs)

@app.route("/logout")
def store_admin_logout():
    session.clear()
    return redirect(url_for("store_admin_login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
