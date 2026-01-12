# ===== services/user/app.py (유저 서비스) =====
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
from shared.auth import require_login

app = Flask(__name__, 
            template_folder='templates',
            static_folder='../../static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "golf_app_secret_key_change_in_production")

# 데이터베이스 초기화
database.init_db()

# =========================
# 루트 경로 (헬스체크용)
# =========================
@app.route("/")
def index():
    return redirect(url_for("login"))

# =========================
# 유저 회원가입
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        birth_date = request.form.get("birth_date")
        gender = request.form.get("gender")
        password = request.form.get("password")

        # 필수 항목 확인
        if not all([name, phone, birth_date, gender, password]):
            return render_template("user_signup.html", error="모든 항목을 입력해주세요.")
        
        # 휴대폰번호를 아이디로 사용 (하이픈 제거)
        user_id = phone.replace("-", "").replace(" ", "")
        
        try:
            database.create_user(user_id, password, name, phone, gender, birth_date)
            return redirect(url_for("login"))
        except ValueError as e:
            return render_template("user_signup.html", error=str(e))
        except Exception as e:
            return render_template("user_signup.html", error=f"회원가입 실패: {str(e)}")

    return render_template("user_signup.html")

# =========================
# 유저 로그인 (아이디/비밀번호만)
# =========================
@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        uid = request.form.get("user_id")
        pw = request.form.get("password")

        # 사용자 인증
        user = database.check_user(uid, pw)
        if not user:
            return render_template("user_login.html", error="아이디 또는 비밀번호가 틀렸습니다.")

        # 로그인 성공 - 세션에 사용자 정보만 저장 (매장/타석은 아직 선택 안함)
        session["user_id"] = uid
        session["role"] = "user"
        
        # 매장/타석 선택 화면으로 이동
        return redirect(url_for("select_store_bay"))

    # GET 요청 시 로그인 페이지 표시
    return render_template("user_login.html")

# =========================
# 매장/타석 선택 화면
# =========================
@app.route("/select-store-bay", methods=["GET", "POST"])
@require_login
def select_store_bay():
    if request.method == "POST":
        store_id = request.form.get("store_id")
        bay_id = request.form.get("bay_id")
        
        if not store_id or not bay_id:
            stores = database.get_all_stores()
            return render_template("select_store_bay.html", 
                                 stores=stores, 
                                 error="매장과 타석을 선택해주세요.")
        
        # 타석 사용 가능 여부 확인
        active_user = database.get_bay_active_user_info(store_id, bay_id)
        uid = session["user_id"]
        
        if active_user and active_user["user_id"] != uid:
            # 다른 사용자가 사용 중
            stores = database.get_all_stores()
            return render_template("select_store_bay.html", 
                                 stores=stores,
                                 selected_store_id=store_id,
                                 selected_bay_id=bay_id,
                                 error=f"{bay_id}번 타석은 현재 사용 중입니다.")
        
        # 매장/타석 선택 완료 - 세션에 저장
        session["store_id"] = store_id
        session["bay_id"] = bay_id
        
        # 활성 세션 등록
        database.set_active_session(store_id, bay_id, uid)
        
        # 메인 페이지로 이동
        return redirect(url_for("user_main"))
    
    # GET 요청 시 매장/타석 선택 페이지 표시
    stores = database.get_all_stores()
    return render_template("select_store_bay.html", stores=stores)

# =========================
# 유저 메인
# =========================
@app.route("/main")
@require_login
def user_main():
    uid = session["user_id"]
    user = database.get_user(uid)
    last_shot = database.get_last_shot(uid)
    dates = database.get_user_practice_dates(uid)
    stores = database.get_all_stores()

    return render_template("user_main.html",
                         user=user,
                         last_shot=last_shot,
                         dates=dates,
                         stores=stores)

# =========================
# 유저 전체 샷 리스트
# =========================
@app.route("/shots")
@require_login
def user_shots():
    from .utils import classify_by_criteria
    
    uid = session["user_id"]
    rows = database.get_all_shots(uid)

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

    return render_template("shots_all.html", shots=shots)

# =========================
# 로그아웃
# =========================
@app.route("/logout")
@require_login
def logout():
    store_id = session.get("store_id")
    bay_id = session.get("bay_id")
    
    if store_id and bay_id:
        database.clear_active_session(store_id, bay_id)
    
    session.clear()
    return redirect(url_for("login"))

# =========================
# API: 타석 코드 확인
# =========================
@app.route("/api/check_bay_code", methods=["POST"])
def check_bay_code():
    """타석 코드 유효성 확인 API"""
    data = request.get_json()
    bay_code = data.get("bay_code", "").strip().upper()
    
    if not bay_code:
        return jsonify({"valid": False, "message": "타석 코드를 입력하세요."})
    
    store_bay = database.get_store_bay_by_code(bay_code)
    if store_bay:
        return jsonify({
            "valid": True,
            "store_id": store_bay["store_id"],
            "bay_id": store_bay["bay_id"],
            "message": "타석 코드가 확인되었습니다."
        })
    else:
        return jsonify({"valid": False, "message": "유효하지 않은 타석 코드입니다."})

@app.route("/api/get_bays", methods=["GET"])
@require_login
def get_bays_api():
    """매장의 타석 목록 조회 API"""
    store_id = request.args.get("store_id")
    if not store_id:
        return jsonify({"bays": []}), 400
    
    bays = database.get_bays(store_id)
    return jsonify({"bays": bays})

# =========================
# API: 샷 데이터 저장 (main.py에서 사용)
# =========================
@app.route("/api/save_shot", methods=["POST"])
def save_shot():
    data = request.json
    print("📥 서버 수신 데이터:", data)
    database.save_shot_to_db(data)
    return jsonify({"status": "ok"})

# =========================
# API: 활성 사용자 조회 (main.py에서 사용)
# =========================
@app.route("/api/active_user", methods=["GET"])
def get_active_user():
    store_id = request.args.get("store_id")
    bay_id = request.args.get("bay_id")
    
    if not store_id or not bay_id:
        return jsonify({"error": "store_id and bay_id required"}), 400
    
    active_user = database.get_active_user(store_id, bay_id)
    return jsonify(active_user if active_user else {})

# =========================
# API: 세션 삭제 (main.py에서 사용)
# =========================
@app.route("/api/clear_session", methods=["POST"])
def clear_session():
    data = request.get_json() or {}
    store_id = data.get("store_id") or request.args.get("store_id")
    bay_id = data.get("bay_id") or request.args.get("bay_id")
    
    if store_id and bay_id:
        deleted = database.clear_active_session(store_id, bay_id)
        return jsonify({"success": True, "deleted": deleted})
    return jsonify({"success": False, "error": "store_id and bay_id required"}), 400

# =========================
# API: 매장 PC 등록
# =========================
@app.route("/api/register_pc", methods=["POST"])
def register_pc():
    """매장 PC 등록 API"""
    data = request.get_json()
    
    store_name = data.get("store_name")
    bay_name = data.get("bay_name")
    pc_name = data.get("pc_name")
    pc_info = data.get("pc_info")
    
    if not all([store_name, bay_name, pc_name, pc_info]):
        return jsonify({
            "success": False,
            "message": "store_name, bay_name, pc_name, pc_info 모두 필요합니다."
        }), 400
    
    if database.register_store_pc(store_name, bay_name, pc_name, pc_info):
        return jsonify({
            "success": True,
            "message": "PC 등록 성공",
            "pc_unique_id": pc_info.get("unique_id")
        })
    else:
        return jsonify({
            "success": False,
            "message": "PC 등록 실패"
        }), 500

@app.route("/api/update_pc_last_seen", methods=["POST"])
def update_pc_last_seen():
    """PC 마지막 접속 시간 업데이트 API"""
    data = request.get_json()
    pc_unique_id = data.get("pc_unique_id")
    
    if not pc_unique_id:
        return jsonify({"success": False, "message": "pc_unique_id 필요"}), 400
    
    database.update_pc_last_seen(pc_unique_id)
    return jsonify({"success": True})

@app.route("/api/check_pc_approval", methods=["GET"])
def check_pc_approval():
    """PC 승인 상태 확인 API"""
    pc_unique_id = request.args.get("pc_unique_id")
    
    if not pc_unique_id:
        return jsonify({"approved": False, "message": "pc_unique_id 필요"}), 400
    
    approved = database.is_pc_approved(pc_unique_id)
    if approved:
        return jsonify({"approved": True, "message": "승인됨"})
    else:
        pc_info = database.get_store_pc_by_unique_id(pc_unique_id)
        if not pc_info:
            return jsonify({"approved": False, "message": "등록되지 않은 PC입니다."})
        elif pc_info.get("status") == "pending":
            return jsonify({"approved": False, "message": "승인 대기 중입니다."})
        elif pc_info.get("status") == "rejected":
            return jsonify({"approved": False, "message": "거부된 PC입니다."})
        else:
            return jsonify({"approved": False, "message": "사용기간이 만료되었거나 비활성 상태입니다."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
