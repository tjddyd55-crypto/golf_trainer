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

# Static 폴더 경로: 로컬 static 폴더 우선, 없으면 상위 static 폴더
static_path = os.path.join(current_dir, 'static')
if not os.path.exists(static_path):
    static_path = os.path.join(current_dir, '../../static')
    if not os.path.exists(static_path):
        static_path = 'static'  # 기본값

app = Flask(__name__, 
            template_folder='templates',
            static_folder=static_path)

# 🔒 보안: Secret Key 환경 변수 필수
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
if not FLASK_SECRET_KEY:
    print("[WARNING] FLASK_SECRET_KEY 환경 변수가 설정되지 않았습니다. 프로덕션에서는 보안 위험이 있습니다.", flush=True)
    FLASK_SECRET_KEY = "golf_app_secret_key_change_in_production"  # 개발용 기본값
app.secret_key = FLASK_SECRET_KEY

# 데이터베이스 초기화
database.init_db()

# =========================
# 매장 관리자 회원가입
# =========================
def validate_store_id(store_id):
    """매장코드 형식 검증"""
    import re
    if not re.match(r'^[A-Z][A-Z0-9]{3,9}$', store_id):
        return False, "매장코드는 영문 대문자로 시작하고, 영문자와 숫자만 사용 가능합니다. (4-10자)"
    return True, None

@app.route("/signup", methods=["GET", "POST"])
def store_admin_signup():
    if request.method == "POST":
        # 필수 항목
        store_id = request.form.get("store_id", "").strip().upper()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        store_name = request.form.get("store_name", "").strip()
        contact = request.form.get("contact", "").strip()
        business_number = request.form.get("business_number", "").strip()
        bays_count = int(request.form.get("bays_count", "1") or "1")
        
        # 타석 수 검증
        if bays_count < 1 or bays_count > 50:
            return render_template("store_admin_signup.html", 
                                 error="타석(룸) 수는 1개 이상 50개 이하여야 합니다.")
        
        # 선택 항목
        owner_name = request.form.get("owner_name", "").strip() or None
        birth_date = request.form.get("birth_date", "").strip() or None
        email = request.form.get("email", "").strip() or None
        address = request.form.get("address", "").strip() or None
        
        # 매장코드 검증
        is_valid, error_msg = validate_store_id(store_id)
        if not is_valid:
            return render_template("store_admin_signup.html", error=error_msg)
        
        # 비밀번호 확인
        if password != password_confirm:
            return render_template("store_admin_signup.html", 
                                 error="비밀번호가 일치하지 않습니다.")
        
        # 매장코드 중복 체크
        if database.check_store_id_exists(store_id):
            return render_template("store_admin_signup.html", 
                                 error="이미 사용 중인 매장코드입니다.")
        
        # 매장 등록
        try:
            result = database.create_store(
                store_id, store_name, password, contact, business_number,
                owner_name, birth_date, email, address, bays_count
            )
            if result is True:
                return render_template("store_register_success.html", 
                                     message="매장 등록 요청이 접수되었습니다. 관리자 승인 후 사용 가능합니다.")
            elif isinstance(result, tuple) and len(result) == 2:
                # (False, "오류 메시지") 형식
                return render_template("store_admin_signup.html", 
                                     error=f"매장 등록 실패: {result[1]}")
            else:
                return render_template("store_admin_signup.html", 
                                     error="매장 등록 실패. 다시 시도해주세요.")
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] 매장 등록 예외 발생: {error_trace}")
            return render_template("store_admin_signup.html", 
                                 error=f"매장 등록 실패: {str(e)}")

    return render_template("store_admin_signup.html")

# =========================
# 매장 관리자 로그인
# =========================
@app.route("/login", methods=["GET", "POST"])
def store_admin_login():
    if request.method == "POST":
        try:
            store_id = request.form.get("store_id", "").strip()
            password = request.form.get("password", "")

            # 1️⃣ 매장 계정 검증
            store = database.check_store(store_id, password)
            if not store:
                return render_template("store_admin_login.html", 
                                     error="매장 코드 또는 비밀번호가 틀렸습니다.")
            
            # 매장 상태 확인
            store_status = store.get("status", "pending")
            if store_status == "pending":
                return render_template("store_admin_login.html", 
                                     error="매장 등록 요청이 승인 대기 중입니다. 승인 후 로그인할 수 있습니다.")
            elif store_status == "rejected":
                return render_template("store_admin_login.html", 
                                     error="매장 등록이 거부되었습니다. 관리자에게 문의하세요.")

            # 2️⃣ 타석(PC) 유효성 판정 (최적화된 쿼리)
            from datetime import date
            today = date.today()
            
            try:
                pc_summary = database.get_pc_status_summary(store_id)
                valid_count = pc_summary.get("valid_count", 0) if pc_summary else 0
                total_count = pc_summary.get("total_count", 0) if pc_summary else 0
                last_expiry = pc_summary.get("last_expiry") if pc_summary else None
            except Exception as e:
                # PC 상태 조회 실패 시 기본값 사용
                import traceback
                print(f"[ERROR] get_pc_status_summary failed: {e}")
                print(traceback.format_exc())
                valid_count = 0
                total_count = 0
                last_expiry = None
            
            # 3️⃣ 로그인 결과 분기
            session["store_id"] = store_id
            session["role"] = "store_admin"
            
            if valid_count > 0:
                # Case A: 유효 타석 1개 이상 → 정상 모드
                session["readonly_mode"] = False
                return redirect(url_for("store_admin_dashboard"))
            elif total_count > 0:
                # Case B: 유효 타석 0개 → 읽기 전용 모드
                session["readonly_mode"] = True
                session["readonly_reason"] = "no_valid_pc"
                if last_expiry:
                    session["last_expiry"] = last_expiry.isoformat() if hasattr(last_expiry, 'isoformat') else str(last_expiry)
                return redirect(url_for("store_admin_dashboard"))
            else:
                # Case C: 등록된 타석 없음 → 읽기 전용 모드
                session["readonly_mode"] = True
                session["readonly_reason"] = "no_pc"
                return redirect(url_for("store_admin_dashboard"))
        
        except Exception as e:
            # 로그인 과정에서 발생한 모든 오류 처리
            import traceback
            error_msg = str(e)
            traceback.print_exc()
            print(f"[ERROR] store_admin_login failed: {error_msg}")
            return render_template("store_admin_login.html", 
                                 error=f"로그인 중 오류가 발생했습니다: {error_msg}")

    return render_template("store_admin_login.html")

# =========================
# 매장 관리자 대시보드
# =========================
@app.route("/")
@require_role("store_admin")
def store_admin_dashboard():
    try:
        from utils import classify_by_criteria
        
        store_id = session.get("store_id")
        bays = database.get_bays(store_id)
        active_sessions = database.get_all_active_sessions(store_id)
        rows = database.get_all_shots_by_store(store_id)
        
        # 매장 정보 조회 (전체 타석 수)
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT bays_count FROM stores WHERE store_id = %s", (store_id,))
        store = cur.fetchone()
        total_bays_count = store["bays_count"] if store else 0
        cur.close()
        conn.close()
        
        # 유효한 타석 수 계산
        valid_bays_count = sum(1 for bay in bays if bay.get("is_valid", False))
        invalid_bays_count = total_bays_count - valid_bays_count
        
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
        
        # 각 타석에 활성 사용자 정보 추가
        for bay in bays:
            bay_key = f"{store_id}_{bay['bay_id']}"
            if bay_key in bay_active_users:
                bay['active_user'] = bay_active_users[bay_key].get('user_id')
                bay['login_time'] = bay_active_users[bay_key].get('login_time')
            else:
                bay['active_user'] = None
                bay['login_time'] = None

        return render_template("store_admin_dashboard.html",
                             store_id=store_id,
                             bays=bays,
                             active_sessions=active_sessions,
                             bay_active_users=bay_active_users,
                             shots=shots,
                             total_bays_count=total_bays_count,
                             valid_bays_count=valid_bays_count,
                             invalid_bays_count=invalid_bays_count)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

# =========================
# 타석별 샷 기록
# =========================
@app.route("/bay/<store_id>/<bay_id>")
@require_role("store_admin")
def bay_shots(store_id, bay_id):
    try:
        from utils import classify_by_criteria
        
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] bay_shots failed: {str(e)}")
        return f"오류 발생: {str(e)}", 500

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
# 타석 표시 형식 통일 헬퍼 함수
# =========================
def format_bay_display(bay_number=None, bay_name=None, bay_id=None):
    """
    bay 표시 형식 통일: bay_name 우선, 없으면 "{bay_number}번 타석(룸)"
    bay_id는 내부 키이므로 화면에 출력하지 않음
    """
    # bay_name이 있으면 우선 사용
    if bay_name and bay_name.strip():
        return bay_name.strip()
    
    # bay_number가 있으면 번호로 표시
    if bay_number:
        return f"{bay_number}번 타석(룸)"
    
    # bay_id가 숫자면 번호로 간주 (레거시 지원)
    if bay_id:
        try:
            bay_num = int(bay_id)
            return f"{bay_num}번 타석(룸)"
        except (ValueError, TypeError):
            pass
    
    return "타석 정보 없음"

# =========================
# 로그아웃
# =========================
@app.route("/pcs")
@require_role("store_admin")
def manage_pcs():
    """매장 타석(룸) 관리"""
    try:
        store_id = session.get("store_id")
        
        if not store_id:
            return redirect(url_for("store_admin_login"))
        
        # 매장 이름 조회
        from psycopg2.extras import RealDictCursor
        conn = None
        cur = None
        try:
            conn = database.get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT store_name FROM stores WHERE store_id = %s", (store_id,))
            store = cur.fetchone()
            store_name = store["store_name"] if store and store.get("store_name") else store_id
        except Exception as e:
            print(f"매장 정보 조회 오류: {e}")
            store_name = store_id
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        
        # 해당 매장의 PC 목록 조회
        try:
            pcs = database.get_store_pcs_by_store(store_name)
        except Exception as e:
            print(f"PC 목록 조회 오류: {e}")
            import traceback
            traceback.print_exc()
            pcs = []
        
        # 각 PC에 표시용 bay_display 추가 및 만료 여부 계산
        from datetime import date
        today = date.today()
        
        for pc in pcs:
            try:
                # bay_number 우선 사용 (새로운 방식)
                pc["bay_display"] = format_bay_display(
                    bay_number=pc.get("bay_number"),
                    bay_name=pc.get("bay_name"),
                    bay_id=pc.get("bay_id")  # 레거시 지원
                )
                
                # 만료 여부 계산
                pc["is_expired"] = False
                usage_end_date = pc.get("usage_end_date")
                if usage_end_date:
                    if isinstance(usage_end_date, str):
                        try:
                            usage_end_date = date.fromisoformat(usage_end_date.split(' ')[0])
                        except:
                            usage_end_date = None
                    if usage_end_date and usage_end_date < today:
                        pc["is_expired"] = True
                
                # 상태 통일: APPROVED / PENDING / EXPIRED
                if pc.get("status") == "active" and not pc["is_expired"]:
                    pc["display_status"] = "APPROVED"
                elif pc.get("status") == "pending":
                    pc["display_status"] = "PENDING"
                elif pc["is_expired"] or pc.get("status") != "active":
                    pc["display_status"] = "EXPIRED"
                else:
                    pc["display_status"] = "PENDING"
                    
            except Exception as e:
                print(f"bay_display 생성 오류: {e}")
                pc["bay_display"] = "타석 정보 없음"
                pc["is_expired"] = False
                pc["display_status"] = "PENDING"
        
        return render_template("manage_pcs.html",
                             store_id=store_id,
                             store_name=store_name,
                             pcs=pcs)
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        print(f"manage_pcs 전체 오류: {error_msg}")
        return f"오류 발생: {error_msg}", 500

# =========================
# API: PC 연장 요청 (CRITICAL 2 - STORE_ADMIN만)
# =========================
@app.route("/api/pcs/<pc_unique_id>/extension-request", methods=["POST"])
@require_role("store_admin")
def create_extension_request(pc_unique_id):
    """PC 연장 요청 생성 - STORE_ADMIN만 가능"""
    try:
        store_id = session.get("store_id")
        requested_by = session.get("store_id")  # store_id를 requested_by로 사용
        
        data = request.get_json() or {}
        requested_until = data.get("requested_until")
        reason = data.get("reason")
        
        if not requested_until:
            return jsonify({"success": False, "message": "requested_until이 필요합니다."}), 400
        
        # PC가 해당 매장 소속인지 확인
        pc_info = database.get_store_pc_by_unique_id(pc_unique_id)
        if not pc_info:
            return jsonify({"success": False, "message": "PC를 찾을 수 없습니다."}), 404
        
        pc_store_id = pc_info.get("store_id")
        if pc_store_id and pc_store_id != store_id:
            return jsonify({"success": False, "message": "권한이 없습니다."}), 403
        
        # 연장 요청 생성
        request_id, error = database.create_extension_request(
            pc_unique_id, store_id, requested_by, requested_until, reason
        )
        
        if error:
            return jsonify({"success": False, "message": error}), 400 if "이미" in error else 409
        
        # Audit 로그
        from flask import request as flask_request
        database.log_audit(
            actor_role="store_admin",
            actor_id=store_id,
            action="CREATE_EXTENSION_REQUEST",
            target_type="pc",
            target_id=pc_unique_id,
            after_state={"request_id": request_id, "requested_until": requested_until},
            ip_address=flask_request.remote_addr,
            user_agent=flask_request.headers.get("User-Agent")
        )
        
        return jsonify({"success": True, "request_id": request_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/stores/<store_id>/pc-extension-requests", methods=["GET"])
@require_role("store_admin")
def get_extension_requests(store_id):
    """연장 요청 목록 조회"""
    try:
        # STORE_ADMIN은 자신의 매장 요청만 조회 가능
        current_store_id = session.get("store_id")
        if store_id != current_store_id:
            return jsonify({"error": "권한이 없습니다."}), 403
        
        requests = database.get_extension_requests(store_id=store_id)
        return jsonify({"requests": requests})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =========================
# 보안: STORE_ADMIN이 직접 승인/기간 변경 차단 (CRITICAL 2)
# =========================
@app.route("/api/pcs/<pc_unique_id>/approve", methods=["POST"])
@require_role("store_admin")
def block_store_admin_approve(pc_unique_id):
    """STORE_ADMIN은 직접 승인 불가 - 403 반환"""
    return jsonify({"error": "매장 관리자는 직접 승인할 수 없습니다. 연장 요청을 사용하세요."}), 403

@app.route("/api/pcs/<pc_unique_id>/reject", methods=["POST"])
@require_role("store_admin")
def block_store_admin_reject(pc_unique_id):
    """STORE_ADMIN은 직접 반려 불가 - 403 반환"""
    return jsonify({"error": "매장 관리자는 직접 반려할 수 없습니다."}), 403

@app.route("/api/pcs/<pc_unique_id>/update-usage", methods=["POST", "PUT"])
@require_role("store_admin")
def block_store_admin_update_usage(pc_unique_id):
    """STORE_ADMIN은 직접 기간 변경 불가 - 403 반환"""
    return jsonify({"error": "매장 관리자는 직접 기간을 변경할 수 없습니다. 연장 요청을 사용하세요."}), 403

@app.route("/logout")
def store_admin_logout():
    session.clear()
    return redirect(url_for("store_admin_login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
