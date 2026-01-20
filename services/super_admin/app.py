# ===== services/super_admin/app.py (총책임자 서비스) =====
# ✅ [1단계] 서비스 부팅 확인 로그 (가장 먼저 출력)
import os
import sys
print("### SUPER_ADMIN BOOT START ###", flush=True)
print("### SERVICE=super_admin ###", flush=True)
print("### PORT env =", os.getenv("PORT"), flush=True)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import re
import traceback
from datetime import datetime

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

# =========================
# 🔒 보안 설정
# =========================
# Secret Key: 환경 변수 필수 (프로덕션에서는 반드시 설정)
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
if not FLASK_SECRET_KEY:
    print("[WARNING] FLASK_SECRET_KEY 환경 변수가 설정되지 않았습니다. 프로덕션에서는 보안 위험이 있습니다.", flush=True)
    FLASK_SECRET_KEY = "golf_app_secret_key_change_in_production"  # 개발용 기본값
app.secret_key = FLASK_SECRET_KEY

# 세션 보안 설정
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'  # HTTPS 강제 (프로덕션)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript 접근 차단
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF 보호
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30분

# 보안 헤더 추가
@app.after_request
def set_security_headers(response):
    """모든 응답에 보안 헤더 추가"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'  # HTTPS 강제
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# =========================
# ✅ [2단계] Healthcheck 엔드포인트 (app 생성 직후 즉시 등록)
# Railway Healthcheck용 - 무조건 200 OK 반환 (외부 의존성 체크 절대 금지)
# 로그 최소화: Railway 헬스체크는 자주 호출되므로 로그 출력 제거
# =========================
@app.route("/health", methods=["GET"])
def health():
    """Railway healthcheck용 엔드포인트 - 인증 불필요, DB 접근 불필요"""
    # Railway 헬스체크는 자주 호출되므로 로그 출력 제거 (로그 폭주 방지)
    return "OK", 200

# 데이터베이스 초기화 (healthcheck 이후)
try:
    database.init_db()
except Exception as e:
    print(f"[WARNING] Database initialization failed: {e}", flush=True)
    # 데이터베이스 초기화 실패해도 애플리케이션은 기동 가능

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
# 총책임자 로그인
# =========================
@app.route("/login", methods=["GET", "POST"])
def super_admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # 총책임자 인증 (환경 변수 또는 하드코딩)
        super_admin_username = os.environ.get("SUPER_ADMIN_USERNAME", "admin")
        super_admin_password = os.environ.get("SUPER_ADMIN_PASSWORD", "endolpin0!")
        
        if username == super_admin_username and password == super_admin_password:
            session["role"] = "super_admin"
            session["user_id"] = "super_admin"
            return redirect(url_for("super_admin_dashboard"))
        else:
            return render_template("super_admin_login.html", error="인증 실패")

    return render_template("super_admin_login.html")

# =========================
# 총책임자 대시보드
# =========================
@app.route("/")
@require_role("super_admin")
def super_admin_dashboard():
    try:
        from datetime import date
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM stores ORDER BY requested_at DESC NULLS LAST, store_id")
        stores = [dict(row) for row in cur.fetchall()]
        
        # 각 매장의 유효한 타석 수 계산
        today = date.today()
        for store in stores:
            store_id = store.get("store_id")
            total_bays = store.get("bays_count", 0)
            
            # 유효한 PC 개수 계산 (status='active'이고 사용 기간이 유효한 경우)
            cur.execute("""
                SELECT COUNT(*) as valid_count
                FROM store_pcs
                WHERE store_id = %s
                  AND status = 'active'
                  AND (usage_end_date IS NULL OR usage_end_date >= %s)
            """, (store_id, today))
            result = cur.fetchone()
            valid_count = result['valid_count'] if result else 0
            
            store['valid_bays_count'] = valid_count
            store['total_bays_count'] = total_bays
        
        cur.close()
        conn.close()
        
        # 통계 정보
        stats = {
            "total_stores": len(stores),
            "active_stores": len([s for s in stores if s.get("subscription_status") == "active"]),
            "expired_stores": len([s for s in stores if s.get("subscription_status") == "expired"]),
            "pending_stores": len([s for s in stores if s.get("status") == "pending"]),
        }
        
        # Emergency 모드 상태 전달
        emergency_mode = session.get("emergency_mode", False)
        
        return render_template("super_admin_dashboard.html",
                             emergency_mode=emergency_mode,
                             stores=stores,
                             stats=stats)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

# =========================
# 매장 관리
# =========================
@app.route("/stores/<store_id>/bays")
@require_role("super_admin")
def store_bays_detail(store_id):
    """매장별 타석 현황 상세 페이지"""
    try:
        from datetime import date
        from psycopg2.extras import RealDictCursor
        import re
        
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 매장 정보 조회
        cur.execute("SELECT * FROM stores WHERE store_id = %s", (store_id,))
        store = cur.fetchone()
        if not store:
            return "매장을 찾을 수 없습니다.", 404
        
        store = dict(store)
        total_bays_count = store.get("bays_count", 0)
        store_name = store.get("store_name", "")
        today = date.today()
        
        # 전체 타석 목록 생성
        all_bays = []
        for i in range(1, total_bays_count + 1):
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
                "pc_name": None,
                "pc_unique_id": None,
                "usage_start_date": None,
                "usage_end_date": None,
                "approved_at": None,
                "approved_by": None,
                "notes": None
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
            for bay in all_bays:
                if bay["bay_id"] == bay_id:
                    bay.update(dict(db_bay))
                    break
        
        # 각 타석의 PC 등록 상태 및 유효성 확인 (store_id와 bay_id로 직접 매칭)
        cur.execute("""
            SELECT bay_id, bay_name, pc_name, pc_unique_id, status, usage_start_date, usage_end_date, 
                   approved_at, approved_by, notes
            FROM store_pcs
            WHERE store_id = %s
        """, (store_id,))
        pcs = cur.fetchall()
        
        # bay_id로 직접 매칭 (더 정확함)
        for pc in pcs:
            pc_bay_id = pc.get("bay_id")
            if not pc_bay_id:
                # bay_id가 없으면 bay_name에서 추출
                bay_name = pc.get("bay_name", "")
                match = re.search(r'(\d+)', str(bay_name))
                if match:
                    pc_bay_id = f"{int(match.group(1)):02d}"
                else:
                    continue
            
            # bay_id로 매칭
            for bay in all_bays:
                if bay["bay_id"] == pc_bay_id:
                    bay["has_pc"] = True
                    bay["pc_status"] = pc.get("status")
                    bay["pc_name"] = pc.get("pc_name")
                    bay["pc_unique_id"] = pc.get("pc_unique_id")
                    bay["usage_start_date"] = pc.get("usage_start_date")
                    bay["usage_end_date"] = pc.get("usage_end_date")
                    bay["approved_at"] = pc.get("approved_at")
                    bay["approved_by"] = pc.get("approved_by")
                    bay["notes"] = pc.get("notes")
                    
                    # 유효성 판정
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
                            bay["is_valid"] = True
                    break
        
        # 유효한 타석 수 계산
        valid_bays_count = sum(1 for bay in all_bays if bay.get("is_valid", False))
        
        # 모든 매장 목록 (드롭다운용)
        cur.execute("SELECT store_id, store_name FROM stores ORDER BY store_name, store_id")
        all_stores = [dict(row) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        # 슈퍼 관리자 대리 조회: 매장 관리자 대시보드 템플릿 재사용
        # store_admin의 dashboard 로직과 동일하게 데이터 준비
        from datetime import date
        today = date.today()
        
        # 활성 세션 조회
        active_sessions = database.get_all_active_sessions(store_id)
        
        # 샷 데이터 조회
        rows = database.get_all_shots_by_store(store_id)
        shots = []
        for r in rows[:20]:  # 최근 20개만
            s = dict(r)
            shots.append(s)
        
        # 타석별 활성 사용자 매핑
        bay_active_users = {}
        for session_info in active_sessions:
            key = f"{session_info['store_id']}_{session_info['bay_id']}"
            bay_active_users[key] = session_info
        
        # 각 타석에 활성 사용자 정보 추가
        for bay in all_bays:
            bay_key = f"{store_id}_{bay['bay_id']}"
            if bay_key in bay_active_users:
                bay['active_user'] = bay_active_users[bay_key].get('user_id')
                bay['login_time'] = bay_active_users[bay_key].get('login_time')
            else:
                bay['active_user'] = None
                bay['login_time'] = None
        
        # 슈퍼 관리자 대리 조회: 매장 관리자 대시보드 템플릿 재사용
        return render_template("store_admin_dashboard_impersonate.html",
                             store_id=store_id,
                             bays=all_bays,
                             active_sessions=active_sessions,
                             bay_active_users=bay_active_users,
                             shots=shots,
                             total_bays_count=total_bays_count,
                             valid_bays_count=valid_bays_count,
                             invalid_bays_count=total_bays_count - valid_bays_count,
                             isImpersonating=True,
                             readOnly=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

@app.route("/bay/<store_id>/<bay_id>")
@require_role("super_admin")
def bay_shots(store_id, bay_id):
    """타석별 샷 기록 조회 (Super Admin)"""
    try:
        # store_admin의 utils 사용
        store_admin_dir = os.path.join(current_dir, '../store_admin')
        if store_admin_dir not in sys.path:
            sys.path.insert(0, store_admin_dir)
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
            s["back_spin_class"] = classify_by_criteria(bk, club_id, "back_spin", fallback_good=None)
            
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
# API: PC 연장 요청 승인/반려 (CRITICAL 2 - SUPER_ADMIN만)
# =========================
@app.route("/api/pcs/<pc_unique_id>/approve", methods=["POST"])
@require_role("super_admin")
def approve_pc_extension(pc_unique_id):
    """PC 연장 요청 승인 - SUPER_ADMIN만 가능"""
    try:
        data = request.get_json() or {}
        approved_until = data.get("approved_until")
        reason = data.get("reason")
        request_id = data.get("request_id")  # 특정 요청 ID (선택)
        
        if not approved_until:
            return jsonify({"success": False, "message": "approved_until이 필요합니다."}), 400
        
        decided_by = session.get("user_id", "super_admin")
        
        # request_id가 있으면 해당 요청 승인, 없으면 가장 최근 REQUESTED 요청 승인
        if request_id:
            success, error = database.approve_extension_request(request_id, decided_by, approved_until, reason)
        else:
            # 가장 최근 REQUESTED 요청 찾기
            requests = database.get_extension_requests(pc_unique_id=pc_unique_id, status="REQUESTED")
            if not requests:
                return jsonify({"success": False, "message": "승인할 요청이 없습니다."}), 404
            request_id = requests[0]["id"]
            success, error = database.approve_extension_request(request_id, decided_by, approved_until, reason)
        
        if not success:
            return jsonify({"success": False, "message": error}), 400
        
        # Audit 로그
        from flask import request as flask_request
        database.log_audit(
            actor_role="super_admin",
            actor_id=decided_by,
            action="APPROVE_EXTENSION_REQUEST",
            target_type="pc",
            target_id=pc_unique_id,
            after_state={"request_id": request_id, "approved_until": approved_until},
            ip_address=flask_request.remote_addr,
            user_agent=flask_request.headers.get("User-Agent")
        )
        
        return jsonify({"success": True, "message": "연장 요청이 승인되었습니다."})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pcs/<pc_unique_id>/reject", methods=["POST"])
@require_role("super_admin")
def reject_pc_extension(pc_unique_id):
    """PC 연장 요청 반려 - SUPER_ADMIN만 가능"""
    try:
        data = request.get_json() or {}
        reason = data.get("reason")
        request_id = data.get("request_id")  # 특정 요청 ID (선택)
        
        decided_by = session.get("user_id", "super_admin")
        
        # request_id가 있으면 해당 요청 반려, 없으면 가장 최근 REQUESTED 요청 반려
        if request_id:
            success, error = database.reject_extension_request(request_id, decided_by, reason)
        else:
            # 가장 최근 REQUESTED 요청 찾기
            requests = database.get_extension_requests(pc_unique_id=pc_unique_id, status="REQUESTED")
            if not requests:
                return jsonify({"success": False, "message": "반려할 요청이 없습니다."}), 404
            request_id = requests[0]["id"]
            success, error = database.reject_extension_request(request_id, decided_by, reason)
        
        if not success:
            return jsonify({"success": False, "message": error}), 400
        
        # Audit 로그
        from flask import request as flask_request
        database.log_audit(
            actor_role="super_admin",
            actor_id=decided_by,
            action="REJECT_EXTENSION_REQUEST",
            target_type="pc",
            target_id=pc_unique_id,
            after_state={"request_id": request_id, "reason": reason},
            ip_address=flask_request.remote_addr,
            user_agent=flask_request.headers.get("User-Agent")
        )
        
        return jsonify({"success": True, "message": "연장 요청이 반려되었습니다."})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/stores/<store_id>/pc-extension-requests", methods=["GET"])
@require_role("super_admin")
def get_all_extension_requests(store_id):
    """모든 연장 요청 목록 조회 - SUPER_ADMIN만"""
    try:
        requests = database.get_extension_requests(store_id=store_id if store_id != "all" else None)
        return jsonify({"requests": requests})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =========================
# Emergency 모드 토글 (CRITICAL 3)
# =========================
@app.route("/api/toggle-emergency", methods=["POST"])
@require_role("super_admin")
def toggle_emergency():
    """Emergency 모드 토글"""
    try:
        current_mode = session.get("emergency_mode", False)
        new_mode = not current_mode
        
        session["emergency_mode"] = new_mode
        
        # Audit 로그
        from flask import request as flask_request
        actor_id = session.get("user_id", "super_admin")
        database.log_audit(
            actor_role="super_admin",
            actor_id=actor_id,
            action="TOGGLE_EMERGENCY_MODE",
            target_type="system",
            after_state={"emergency_mode": new_mode},
            ip_address=flask_request.remote_addr,
            user_agent=flask_request.headers.get("User-Agent")
        )
        
        return jsonify({
            "success": True,
            "emergency_mode": new_mode,
            "message": "Emergency 모드가 활성화되었습니다." if new_mode else "Emergency 모드가 비활성화되었습니다."
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/update_bay_settings", methods=["POST"])
@require_role("super_admin")
def update_bay_settings():
    """타석 설정 업데이트 (기간, 상태 등) - Emergency 모드에서만 허용 (CRITICAL 3)"""
    try:
        # Emergency 모드 체크
        emergency_mode = session.get("emergency_mode", False)
        if not emergency_mode:
            return jsonify({
                "success": False, 
                "message": "Emergency 모드에서만 직접 수정이 가능합니다. 기본 모드에서는 읽기 전용입니다."
            }), 403
        
        # Emergency 모드 사용 시 Audit 로그
        from flask import request as flask_request
        actor_id = session.get("user_id", "super_admin")
        database.log_audit(
            actor_role="super_admin",
            actor_id=actor_id,
            action="EMERGENCY_UPDATE_BAY_SETTINGS",
            target_type="bay",
            ip_address=flask_request.remote_addr,
            user_agent=flask_request.headers.get("User-Agent")
        )
        from datetime import date
        from psycopg2.extras import RealDictCursor
        
        data = request.get_json()
        pc_unique_id = data.get("pc_unique_id")
        bay_id = data.get("bay_id")
        store_id = data.get("store_id")
        usage_start_date = data.get("usage_start_date")
        usage_end_date = data.get("usage_end_date")
        status = data.get("status")
        notes = data.get("notes", "")
        
        if not bay_id or not store_id:
            return jsonify({"success": False, "message": "bay_id와 store_id가 필요합니다."}), 400
        
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 날짜 변환
        start_date = date.fromisoformat(usage_start_date) if usage_start_date else None
        end_date = date.fromisoformat(usage_end_date) if usage_end_date else None
        
        # PC가 등록된 경우: store_pcs 업데이트
        if pc_unique_id:
            cur.execute("""
                UPDATE store_pcs 
                SET bay_id = %s,
                    store_id = %s,
                    usage_start_date = %s,
                    usage_end_date = %s,
                    status = %s,
                    notes = %s
                WHERE pc_unique_id = %s
            """, (bay_id, store_id, start_date, end_date, status, notes, pc_unique_id))
            
            if cur.rowcount == 0:
                return jsonify({"success": False, "message": "등록된 PC를 찾을 수 없습니다."}), 404
        else:
            # PC가 등록되지 않은 타석인 경우: bays 테이블에 타석이 존재하는지 확인하고 생성
            cur.execute("SELECT COUNT(*) as count FROM bays WHERE store_id = %s AND bay_id = %s", (store_id, bay_id))
            bay_exists = cur.fetchone()
            bay_exists_count = bay_exists.get("count", 0) if bay_exists else 0
            if bay_exists_count == 0:
                # 타석 생성
                from shared.database import generate_bay_code
                bay_code = generate_bay_code(store_id, bay_id, cur)
                cur.execute("""
                    INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code)
                    VALUES (%s, %s, 'READY', '', '', %s)
                    ON CONFLICT (store_id, bay_id) DO NOTHING
                """, (store_id, bay_id, bay_code))
        
        # bays 테이블의 status 업데이트 (타석 사용 가능 여부)
        bay_status = "READY" if status == "active" else "BUSY" if status == "pending" else "UNAVAILABLE"
        cur.execute("""
            UPDATE bays 
            SET status = %s
            WHERE store_id = %s AND bay_id = %s
        """, (bay_status, store_id, bay_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "타석 설정이 업데이트되었습니다."})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"타석 설정 업데이트 실패: {str(e)}"}), 500

@app.route("/stores")
@require_role("super_admin")
def manage_stores():
    try:
        from datetime import date
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM stores ORDER BY requested_at DESC NULLS LAST, store_id")
        stores = [dict(row) for row in cur.fetchall()]
        
        # 각 매장의 유효한 타석 수 계산
        today = date.today()
        for store in stores:
            store_id = store.get("store_id")
            total_bays = store.get("bays_count", 0)
            
            # 유효한 PC 개수 계산
            cur.execute("""
                SELECT COUNT(*) as valid_count
                FROM store_pcs
                WHERE store_id = %s
                  AND status = 'active'
                  AND (usage_end_date IS NULL OR usage_end_date >= %s)
            """, (store_id, today))
            result = cur.fetchone()
            valid_count = result['valid_count'] if result else 0
            
            store['valid_bays_count'] = valid_count
            store['total_bays_count'] = total_bays
        
        cur.close()
        conn.close()
        
        return render_template("manage_stores.html", stores=stores)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

# =========================
# 매장 등록 요청 승인
# =========================
@app.route("/store-requests")
@require_role("super_admin")
def store_requests():
    """매장 등록 요청 관리 (승인 대기 + 승인 완료)"""
    try:
        # 승인 대기 중인 매장
        pending_stores = database.get_pending_stores()
        
        # 승인 완료된 매장 (status가 'approved'이거나 NULL인 경우도 포함 - 대시보드와 동일하게)
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # 대시보드와 동일하게 모든 매장 조회 (status 필터 제거)
        cur.execute("""
            SELECT * FROM stores 
            ORDER BY requested_at DESC NULLS LAST, store_id
        """)
        approved_stores = [dict(row) for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        return render_template("store_requests.html", 
                             pending_stores=pending_stores,
                             approved_stores=approved_stores)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

@app.route("/api/approve_store", methods=["POST"])
@require_role("super_admin")
def approve_store():
    """매장 승인"""
    try:
        data = request.get_json()
        store_id = data.get("store_id")
        approved_by = session.get("user_id", "super_admin")
        
        if not store_id:
            return jsonify({"success": False, "message": "store_id가 필요합니다."}), 400
        
        result = database.approve_store(store_id, approved_by)
        if result is True:
            return jsonify({"success": True, "message": "매장이 승인되었습니다."})
        elif isinstance(result, tuple) and len(result) == 2:
            # (False, "오류 메시지") 형식
            return jsonify({"success": False, "message": f"매장 승인 실패: {result[1]}"}), 500
        else:
            return jsonify({"success": False, "message": "매장 승인 실패. 다시 시도해주세요."}), 500
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] approve_store 예외 발생: {error_trace}")
        return jsonify({"success": False, "message": f"매장 승인 실패: {str(e)}"}), 500

@app.route("/api/reject_store", methods=["POST"])
@require_role("super_admin")
def reject_store():
    """매장 거부"""
    data = request.get_json()
    store_id = data.get("store_id")
    approved_by = session.get("user_id", "super_admin")
    
    if not store_id:
        return jsonify({"success": False, "message": "store_id 필요"}), 400
    
    if database.reject_store(store_id, approved_by):
        return jsonify({"success": True, "message": "매장이 거부되었습니다."})
    else:
        return jsonify({"success": False, "message": "매장 거부 실패"}), 500

@app.route("/api/delete_store", methods=["POST"])
@require_role("super_admin")
def delete_store():
    """매장 삭제"""
    data = request.get_json()
    store_id = data.get("store_id")
    
    if not store_id:
        return jsonify({"success": False, "message": "store_id 필요"}), 400
    
    if database.delete_store(store_id):
        return jsonify({"success": True, "message": "매장이 삭제되었습니다."})
    else:
        return jsonify({"success": False, "message": "매장 삭제 실패"}), 500

# =========================
# 결제 관리
# =========================
@app.route("/payments")
@require_role("super_admin")
def manage_payments():
    try:
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM payments ORDER BY payment_date DESC LIMIT 100")
        payments = [dict(row) for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        return render_template("manage_payments.html", payments=payments)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

# =========================
# 사용기간 관리
# =========================
@app.route("/subscriptions")
@require_role("super_admin")
def manage_subscriptions():
    try:
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM subscriptions ORDER BY end_date DESC")
        subscriptions = [dict(row) for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        return render_template("manage_subscriptions.html", subscriptions=subscriptions)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

# =========================
# 매장 구독 연장
# =========================
@app.route("/api/extend_subscription", methods=["POST"])
@require_role("super_admin")
def extend_subscription():
    data = request.get_json()
    store_id = data.get("store_id")
    months = int(data.get("months", 1))
    
    conn = database.get_db_connection()
    cur = conn.cursor()
    
    # 현재 구독 정보 조회
    cur.execute("SELECT end_date FROM stores WHERE store_id = %s", (store_id,))
    result = cur.fetchone()
    
    if result and result[0]:
        from datetime import datetime, timedelta
        current_end = datetime.strptime(result[0], "%Y-%m-%d")
        new_end = current_end + timedelta(days=30 * months)
        new_end_str = new_end.strftime("%Y-%m-%d")
    else:
        from datetime import datetime, timedelta
        new_end = datetime.now() + timedelta(days=30 * months)
        new_end_str = new_end.strftime("%Y-%m-%d")
    
    # 구독 기간 업데이트
    cur.execute(
        "UPDATE stores SET subscription_end_date = %s, subscription_status = 'active' WHERE store_id = %s",
        (new_end_str, store_id)
    )
    
    # 구독 기록 추가
    cur.execute(
        "INSERT INTO subscriptions (store_id, start_date, end_date, status, plan_type) VALUES (%s, %s, %s, 'active', 'monthly')",
        (store_id, datetime.now().strftime("%Y-%m-%d"), new_end_str)
    )
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"success": True, "new_end_date": new_end_str})

# =========================
# 로그아웃
# =========================
@app.route("/pcs")
@require_role("super_admin")
def manage_all_pcs():
    """전체 매장 타석(룸) 관리"""
    try:
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # 모든 상태 조회 (pending, active, rejected 등 모든 상태 포함)
        # deleted_at 같은 삭제 필터 제거, 모든 PC 표시
        cur.execute("""
            SELECT * FROM store_pcs 
            ORDER BY 
                CASE status 
                    WHEN 'pending' THEN 0  -- 승인 대기를 먼저
                    WHEN 'active' THEN 1
                    ELSE 2
                END,
                registered_at DESC
        """)
        pcs = [dict(row) for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        # 각 PC에 표시용 bay_display 추가
        for pc in pcs:
            # bay_number 우선 사용 (새로운 방식)
            pc["bay_display"] = format_bay_display(
                bay_number=pc.get("bay_number"),
                bay_name=pc.get("bay_name"),
                bay_id=pc.get("bay_id")  # 레거시 지원
            )
        
        return render_template("manage_all_pcs.html", pcs=pcs)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

@app.route("/api/approve_pc", methods=["POST"])
@require_role("super_admin")
def approve_pc():
    """PC 승인 (사용 기간 설정 및 타석 정보 설정)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "요청 데이터가 없습니다."}), 400
        
        pc_unique_id = data.get("pc_unique_id")
        store_id = data.get("store_id")  # 매장코드
        bay_id_raw = data.get("bay_id")  # 타석 번호 (bay_number, 정수)
        usage_start_date = data.get("usage_start_date")  # YYYY-MM-DD 문자열
        usage_end_date = data.get("usage_end_date")  # YYYY-MM-DD 문자열
        approved_date = data.get("approved_date")  # YYYY-MM-DD 문자열 (선택)
        notes = data.get("notes", "") or ""
        
        print(f"[DEBUG] approve_pc 요청: pc_unique_id={pc_unique_id}, store_id={store_id}, bay_id_raw={bay_id_raw}")
        
        if not pc_unique_id:
            return jsonify({"success": False, "message": "pc_unique_id가 필요합니다."}), 400
        
        # ✅ 1. bay_number 필수 입력 검증 (bay_id는 실제로 bay_number)
        if not bay_id_raw:
            return jsonify({"success": False, "message": "타석 번호(bay_number)는 필수입니다."}), 400
        
        # ✅ 2. 숫자 여부 검증
        bay_number_str = str(bay_id_raw).strip()
        if not bay_number_str.isdigit():
            return jsonify({"success": False, "message": "타석 번호는 숫자만 입력할 수 있습니다."}), 400
        
        # ✅ 3. 정수 변환 및 범위 체크 (01 입력 시 자동으로 1 처리)
        bay_number = int(bay_number_str)
        if bay_number <= 0:
            return jsonify({"success": False, "message": "타석 번호는 1 이상의 정수여야 합니다."}), 400
        
        print(f"[DEBUG] bay_number 검증 완료: {bay_id_raw} -> {bay_number} (정수)")
        
        # 문자열을 DATE로 변환
        from datetime import date
        try:
            start_date = date.fromisoformat(usage_start_date) if usage_start_date else None
            end_date = date.fromisoformat(usage_end_date) if usage_end_date else None
        except (ValueError, TypeError, AttributeError) as e:
            print(f"[ERROR] 날짜 파싱 오류: {e}")
            return jsonify({
                "success": False,
                "message": "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)"
            }), 400
    except Exception as e:
        print(f"[ERROR] approve_pc 초기 단계 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"요청 처리 중 오류가 발생했습니다: {str(e)}"
        }), 500
    
    # PC 토큰 생성
    from psycopg2.extras import RealDictCursor
    conn = None
    cur = None
    
    try:
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # PC 정보 조회
        cur.execute("SELECT * FROM store_pcs WHERE pc_unique_id = %s", (pc_unique_id,))
        pc_data = cur.fetchone()
        if not pc_data:
            return jsonify({"success": False, "message": "PC를 찾을 수 없습니다."}), 404
        
        pc_data = dict(pc_data)
        mac_address = pc_data.get("mac_address")
        
        print(f"[DEBUG] PC 데이터 조회 완료: store_name={pc_data.get('store_name')}, pc_name={pc_data.get('pc_name')}")
        
        # store_id가 비어있으면 기존 데이터에서 추출 시도
        if not store_id or store_id == '' or store_id == 'null' or store_id is None:
            store_id = None
            # pc_name에서 store_id 추출 시도 (예: "가자스크린골프테스트2-3번룸-PC" -> "가자스크린골프테스트2")
            store_name_from_pc = pc_data.get("store_name", "")
            if store_name_from_pc:
                # store_name에서 store_id 찾기
                cur.execute("SELECT store_id FROM stores WHERE store_name = %s LIMIT 1", (store_name_from_pc,))
                store_row = cur.fetchone()
                if store_row:
                    store_id = store_row[0]
                    print(f"[DEBUG] store_id 자동 추출: {store_id}")
        
        # store_id 검증
        if not store_id or store_id == '' or store_id == 'null':
            if cur:
                cur.close()
            if conn:
                conn.close()
            return jsonify({
                "success": False,
                "message": "매장 정보를 찾을 수 없습니다. store_id가 필요합니다."
            }), 400
        
        # ✅ 4. bay_number 중복 검증 (매장 단위, bay_number 기준)
        # bay_id는 UUID 문자열이므로, bay_number로 중복 검증
        cur.execute("""
            SELECT 1
            FROM store_pcs
            WHERE store_id = %s
              AND bay_number = %s
              AND status = 'active'
              AND pc_unique_id != %s
            LIMIT 1
        """, (store_id, bay_number, pc_unique_id))
        
        duplicate_exists = cur.fetchone() is not None
        if duplicate_exists:
            if cur:
                cur.close()
            if conn:
                conn.close()
            return jsonify({
                "success": False,
                "message": f"타석 번호 {bay_number}는 이미 사용 중입니다. 다른 번호를 입력하세요."
            }), 400
        
        print(f"[DEBUG] bay_number 중복 검증 완료: store_id={store_id}, bay_number={bay_number} (중복 없음)")
        
        # bay_id 조회 또는 생성 (bays 테이블에서 bay_number로 조회)
        cur.execute("""
            SELECT bay_id FROM bays 
            WHERE store_id = %s AND bay_number = %s
            LIMIT 1
        """, (store_id, bay_number))
        bay_row = cur.fetchone()
        
        if bay_row:
            bay_id = bay_row["bay_id"]
        else:
            # bays 테이블에 타석이 없으면 생성 (bay_id는 UUID)
            import uuid
            bay_id = str(uuid.uuid4())[:8]
            bay_code = f"{store_id}_{bay_number}"
            cur.execute("""
                INSERT INTO bays (store_id, bay_id, bay_number, status, user_id, last_update, bay_code)
                VALUES (%s, %s, %s, 'READY', '', CURRENT_TIMESTAMP, %s)
                ON CONFLICT (store_id, bay_id) DO NOTHING
            """, (store_id, bay_id, bay_number, bay_code))
            print(f"[DEBUG] bays 테이블에 타석 생성: store_id={store_id}, bay_id={bay_id}, bay_number={bay_number}")
        
        # 토큰 생성
        pc_token = database.generate_pc_token(pc_unique_id, mac_address)
        
        # 승인일 설정 (제공된 경우 사용, 없으면 오늘)
        try:
            approved_at_value = date.fromisoformat(approved_date) if approved_date else date.today()
        except (ValueError, TypeError):
            approved_at_value = date.today()
        
        # ✅ 5. PC 승인 및 사용 기간 설정 (bay_id와 bay_number 모두 저장)
        # ✅ pc_name은 bay_name과 자동 동기화 (PC 이름 = 타석 이름)
        # 기존 PC 데이터에서 bay_name 조회
        existing_bay_name = pc_data.get("bay_name")
        
        # bay_name이 있으면 pc_name도 동일하게 설정, 없으면 기본값 사용
        pc_name = existing_bay_name or f"{pc_data.get('store_name', '')}-{bay_number}번 타석(룸)"
        
        cur.execute("""
            UPDATE store_pcs 
            SET status = 'active',
                store_id = %s,
                bay_id = %s,
                bay_number = %s,
                pc_name = %s,
                pc_token = %s,
                usage_start_date = %s,
                usage_end_date = %s,
                approved_at = %s,
                approved_by = %s,
                notes = %s
            WHERE pc_unique_id = %s
        """, (store_id, bay_id, bay_number, pc_name, pc_token, start_date, end_date, 
              approved_at_value, session.get("user_id", "super_admin"), notes, pc_unique_id))
        
        conn.commit()
        
        # 승인된 PC 정보 조회
        cur.execute("SELECT * FROM store_pcs WHERE pc_unique_id = %s", (pc_unique_id,))
        pc_data = cur.fetchone()
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "PC 승인 완료",
            "pc_token": pc_data.get("pc_token"),
            "pc": dict(pc_data)
        })
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[ERROR] approve_pc 오류: {error_msg}")
        print(f"[ERROR] Traceback:\n{error_trace}")
        try:
            conn.rollback()
        except:
            pass
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
        return jsonify({
            "success": False, 
            "message": f"PC 승인 실패: {error_msg}",
            "error": error_trace
        }), 500

@app.route("/api/delete_pc", methods=["POST"])
@require_role("super_admin")
def delete_pc():
    """PC 삭제"""
    try:
        data = request.get_json()
        pc_unique_id = data.get("pc_unique_id")
        
        if not pc_unique_id:
            return jsonify({
                "success": False,
                "message": "pc_unique_id가 필요합니다."
            }), 400
        
        # PC 삭제
        success = database.delete_pc(pc_unique_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "PC가 삭제되었습니다."
            })
        else:
            return jsonify({
                "success": False,
                "message": "PC 삭제에 실패했습니다."
            }), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }), 500

@app.route("/api/reject_pc", methods=["POST"])
@require_role("super_admin")
def reject_pc():
    """PC 거부"""
    data = request.get_json()
    pc_unique_id = data.get("pc_unique_id")
    notes = data.get("notes", "")
    
    conn = database.get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE store_pcs 
            SET status = 'blocked', notes = %s
            WHERE pc_unique_id = %s
        """, (notes, pc_unique_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "PC 거부 완료"})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": f"PC 거부 실패: {str(e)}"}), 400

# =========================
# 등록 코드 생성 (golf-api로 프록시)
# =========================
@app.route("/api/create_registration_code", methods=["POST"])
@app.route("/api/create_registration_key", methods=["POST"])  # 하위 호환성
@require_role("super_admin")
def create_registration_code():
    """PC 등록 코드 생성 (golf-api로 프록시)"""
    import requests
    
    # golf-api URL 가져오기
    api_url = os.environ.get("API_URL", "https://golf-api-production-e675.up.railway.app")
    if not api_url.startswith("http"):
        api_url = f"https://{api_url}"
    
    # 슈퍼 관리자 인증 정보
    super_admin_username = os.environ.get("SUPER_ADMIN_USERNAME", "admin")
    super_admin_password = os.environ.get("SUPER_ADMIN_PASSWORD", "endolpin0!")
    
    # 요청 데이터 준비
    data = request.get_json() or {}
    data["username"] = super_admin_username
    data["password"] = super_admin_password
    
    try:
        # golf-api 호출
        response = requests.post(
            f"{api_url}/api/admin/pc-registration-codes",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "success": False,
                "message": f"API 호출 실패: {response.status_code}",
                "error": response.text
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "message": f"API 호출 오류: {str(e)}"
        }), 500

@app.route("/api/registration_codes", methods=["GET"])
@app.route("/api/registration_keys", methods=["GET"])  # 하위 호환성
@require_role("super_admin")
def get_registration_codes():
    """등록 코드 목록 조회 (golf-api로 프록시)"""
    import requests
    
    # golf-api URL 가져오기
    api_url = os.environ.get("API_URL", "https://golf-api-production-e675.up.railway.app")
    if not api_url.startswith("http"):
        api_url = f"https://{api_url}"
    
    # 슈퍼 관리자 인증 정보
    super_admin_username = os.environ.get("SUPER_ADMIN_USERNAME", "admin")
    super_admin_password = os.environ.get("SUPER_ADMIN_PASSWORD", "endolpin0!")
    
    try:
        # golf-api 호출
        response = requests.get(
            f"{api_url}/api/admin/pc-registration-codes",
            params={
                "username": super_admin_username,
                "password": super_admin_password
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "success": False,
                "message": f"API 호출 실패: {response.status_code}",
                "error": response.text
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "message": f"API 호출 오류: {str(e)}"
        }), 500

@app.route("/logout")
def super_admin_logout():
    session.clear()
    return redirect(url_for("super_admin_login"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"### LISTENING ON 0.0.0.0:{port} ###", flush=True)
    app.run(host="0.0.0.0", port=port)
