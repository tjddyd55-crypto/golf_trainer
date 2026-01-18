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

# Static 폴더 경로: 로컬 static 폴더 우선, 없으면 상위 static 폴더
static_path = os.path.join(current_dir, 'static')
if not os.path.exists(static_path):
    static_path = os.path.join(current_dir, '../../static')
    if not os.path.exists(static_path):
        static_path = 'static'  # 기본값

app = Flask(__name__, 
            template_folder='templates',
            static_folder=static_path)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "golf_app_secret_key_change_in_production")

# 데이터베이스 초기화
database.init_db()

# =========================
# 루트 경로 및 메인 페이지
# =========================
@app.route("/")
def index():
    return redirect(url_for("main_page"))

@app.route("/main")
def main_page():
    """메인 페이지 (로그인 전/후 모두 접근 가능)"""
    # 로그인된 경우 매장/타석 선택 페이지로 리다이렉트
    if "user_id" in session:
        # 매장/타석이 선택되지 않은 경우 선택 페이지로
        if not session.get("store_id") or not session.get("bay_id"):
            return redirect(url_for("select_store_bay"))
        # 이미 선택된 경우 메인 대시보드로
        return redirect(url_for("user_main"))
    
    # 로그인 안 된 경우 메인 페이지 표시
    return render_template("main_page.html")

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
    try:
        if request.method == "POST":
            store_id = request.form.get("store_id")
            bay_id = request.form.get("bay_id")
            
            if not store_id or not bay_id:
                stores = database.get_all_stores()
                return render_template("select_store_bay.html", 
                                     stores=stores, 
                                     error="매장과 타석을 선택해주세요.")
            
            # 승인된 타석인지 확인
            approved_bays = database.get_bays(store_id)
            bay_approved = any(bay.get("bay_id") == bay_id for bay in approved_bays)
            
            if not bay_approved:
                # 승인되지 않았거나 만료된 타석: 간단한 경고 메시지와 함께 폼 재표시
                stores = database.get_all_stores()
                return render_template("select_store_bay.html", 
                                     stores=stores,
                                     selected_store_id=store_id,
                                     selected_bay_id=bay_id,
                                     error="완료된 타석입니다. 다른 타석을 이용하세요.")
            
            # 타석 사용 가능 여부 확인 (최근 샷 10분 기준)
            active_user = database.get_bay_active_user_info(store_id, bay_id)
            uid = session["user_id"]
            
            # 최근 샷 기준 정리: 최근 샷이 10분 이상 없으면 active_user 해제
            ttl_minutes = 10  # 최근 샷 10분 기준
            database.cleanup_expired_active_users_by_last_shot(ttl_minutes)
            
            # 정리 후 다시 조회
            active_user = database.get_bay_active_user_info(store_id, bay_id)
            
            if active_user and active_user["user_id"] != uid:
                # 다른 사용자가 사용 중 - 409 Conflict 상황 (TTL 유효)
                stores = database.get_all_stores()
                return render_template("select_store_bay.html", 
                                     stores=stores,
                                     selected_store_id=store_id,
                                     selected_bay_id=bay_id,
                                     error=f"⚠️ {bay_id}번 타석은 현재 다른 사용자가 이용 중입니다. 다른 타석을 선택해주세요."), 409
            
            # 이전 타석의 active_user 해제 (타석 변경 시)
            prev_store_id = session.get("store_id")
            prev_bay_id = session.get("bay_id")
            if prev_store_id and prev_bay_id and (prev_store_id != store_id or prev_bay_id != bay_id):
                database.clear_active_session(prev_store_id, prev_bay_id)
            
            # 매장/타석 선택 완료 - 세션에 저장
            session["store_id"] = store_id
            session["bay_id"] = bay_id
            
            # 활성 세션 등록
            database.set_active_session(store_id, bay_id, uid)
            
            # 메인 대시보드로 이동
            return redirect(url_for("user_main"))
        
        # GET 요청 시 매장/타석 선택 페이지 표시
        stores = database.get_all_stores()
        return render_template("select_store_bay.html", stores=stores)
    except Exception as e:
        import traceback
        traceback.print_exc()
        # HTML 템플릿 엔드포인트는 에러 메시지를 템플릿에 전달
        stores = database.get_all_stores() if 'stores' not in locals() else stores
        return render_template("select_store_bay.html", 
                             stores=stores,
                             error=f"⚠️ 오류가 발생했습니다: {str(e)}"), 500

# =========================
# 유저 메인 대시보드
# =========================
@app.route("/dashboard")
@require_login
def user_main():
    try:
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        # HTML 템플릿 엔드포인트는 에러 메시지를 템플릿에 전달
        return render_template("user_main.html", 
                             user={"user_id": "오류"},
                             last_shot=None,
                             dates=[],
                             stores=[],
                             error=f"⚠️ 오류가 발생했습니다: {str(e)}"), 500

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
    return redirect(url_for("user_login"))

# =========================
# API: 현재 로그인한 유저 정보 조회 (me 기반)
# =========================
@app.route("/api/users/me", methods=["GET"])
@require_login
def get_current_user():
    """현재 로그인한 유저 정보 조회 - 세션의 user_id만 사용"""
    try:
        uid = session["user_id"]
        user = database.get_user(uid)
        if not user:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404
        
        # 비밀번호 제외
        user_data = {k: v for k, v in user.items() if k != "password"}
        return jsonify(user_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/users/me/shots", methods=["GET"])
@require_login
def get_current_user_shots():
    """
    현재 로그인한 유저의 샷 목록 조회 - 세션의 user_id만 사용
    - path/query로 user_id를 절대 받지 않음 (보안 강화)
    - guest 샷은 자동으로 제외됨
    - 빈 배열도 정상 응답 (오류 아님)
    """
    try:
        uid = session["user_id"]
        if not uid:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        
        # 개인 샷 조회 (guest 샷 제외)
        shots = database.get_all_shots(uid)
        
        # 빈 배열도 정상 응답
        return jsonify({"shots": shots if shots else []})
    except KeyError:
        # 세션 만료
        return jsonify({"error": "로그인이 필요합니다."}), 401
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =========================
# 보안: USER role이 다른 userId로 접근 시 차단
# =========================
@app.route("/api/users/me/dashboard", methods=["GET"])
@require_login
def get_user_dashboard():
    """
    유저 대시보드 v3 API (DRIVER 기준, is_valid=TRUE만)
    
    Query Parameters:
        club: DRIVER (기본값), IRON_7, WEDGE (현재는 DRIVER만 구현)
    """
    try:
        uid = session["user_id"]
        if not uid:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        
        club = request.args.get("club", "DRIVER").upper()
        
        # 현재는 DRIVER만 구현
        if club != "DRIVER":
            return jsonify({"error": "현재는 DRIVER만 지원합니다."}), 400
        
        # 유저 성별 조회 (로그용)
        user = database.get_user(uid)
        gender = user.get("gender") if user else None
        
        # 유효 샷 개수 조회 (로그용)
        from datetime import datetime
        from psycopg2.extras import RealDictCursor
        today = datetime.now().strftime("%Y-%m-%d")
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT COUNT(*) as count
            FROM shots
            WHERE user_id = %s AND club_id = 'DRIVER' 
              AND is_valid = TRUE AND is_guest = FALSE 
              AND DATE(timestamp) = %s
        """, (uid, today))
        valid_shots_row = cur.fetchone()
        valid_shots_count = valid_shots_row.get("count", 0) if valid_shots_row else 0
        cur.close()
        conn.close()
        
        # criteria 키 결정 로그 (초기 점검용)
        try:
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from utils import get_criteria_key
            criteria_key = get_criteria_key("DRIVER", gender)
            print(f"[DASHBOARD] user_id={uid}, club={club}, gender={gender}, criteria_key={criteria_key}, valid_shots={valid_shots_count}")
        except Exception as e:
            print(f"[WARNING] criteria key 로그 실패: {e}")
        
        # 1️⃣ 오늘 요약
        today_summary = database.get_today_summary_driver(uid)
        
        # 2️⃣ 최근 샷 (기본 20개)
        recent_shots = database.get_recent_shots_driver(uid, limit=20)
        
        # 3️⃣ 7일 평균 그래프
        last_7_days = database.get_7days_average_driver(uid)
        
        # 4️⃣ 기준값 비교 (최근 7일 평균 vs criteria.json)
        criteria_compare = database.get_criteria_compare_driver(uid)
        
        return jsonify({
            "today_summary": {
                "available_metrics": [
                    "shot_count",
                    "avg_carry",
                    "avg_total_distance",
                    "avg_smash_factor",
                    "avg_face_angle",
                    "avg_club_path",
                    "avg_ball_speed",
                    "avg_club_speed",
                    "avg_back_spin",
                    "avg_side_spin"
                ],
                "values": today_summary
            },
            "recent_shots": {
                "available_metrics": [
                    "carry",
                    "total_distance",
                    "smash_factor",
                    "face_angle",
                    "club_path",
                    "ball_speed",
                    "club_speed",
                    "back_spin",
                    "side_spin",
                    "launch_angle"
                ],
                "shots": recent_shots
            },
            "last_7_days": {
                "available_metrics": [
                    "avg_carry",
                    "avg_total_distance",
                    "avg_smash_factor",
                    "avg_face_angle",
                    "avg_club_path",
                    "avg_ball_speed",
                    "avg_club_speed",
                    "avg_back_spin",
                    "avg_side_spin"
                ],
                "data": last_7_days
            },
            "criteria_compare": {
                "available_metrics": [
                    "carry",
                    "total_distance",
                    "smash_factor",
                    "face_angle",
                    "club_path",
                    "ball_speed",
                    "club_speed",
                    "back_spin",
                    "side_spin"
                ],
                "result": criteria_compare
            }
        })
    except KeyError:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/users/<path:user_id>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@require_login
def block_user_id_access(user_id):
    """USER role은 다른 userId로 접근 불가 - 403 반환"""
    current_user_id = session.get("user_id")
    user_role = session.get("role", "user")
    
    # USER role이면 무조건 차단 (자신의 데이터는 /me로 접근)
    if user_role == "user":
        return jsonify({"error": "접근 권한이 없습니다. /api/users/me를 사용하세요."}), 403
    
    # SUPER_ADMIN이나 STORE_ADMIN은 허용 (향후 확장 가능)
    return jsonify({"error": "이 엔드포인트는 사용할 수 없습니다."}), 404

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
    """타석 활성 세션 해제 (로그아웃/종료 시 사용)"""
    data = request.get_json() or {}
    store_id = data.get("store_id") or request.args.get("store_id")
    bay_id = data.get("bay_id") or request.args.get("bay_id")
    
    if store_id and bay_id:
        deleted = database.clear_active_session(store_id, bay_id)
        return jsonify({"success": True, "deleted": deleted})
    return jsonify({"success": False, "error": "store_id and bay_id required"}), 400

# =========================
# API: 만료된 active_user 자동 정리 (최근 샷 10분 기준)
# =========================
@app.route("/api/cleanup_expired_sessions", methods=["POST"])
def cleanup_expired_sessions():
    """만료된 active_user 자동 정리 (최근 샷 10분 기준)"""
    # TTL: 10분 - 최근 샷이 10분 이상 없으면 해제
    ttl_minutes = int(request.args.get("ttl_minutes", 10))
    
    cleaned_count = database.cleanup_expired_active_users_by_last_shot(ttl_minutes)
    
    return jsonify({
        "success": True,
        "cleaned_count": cleaned_count,
        "ttl_minutes": ttl_minutes
    })

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
