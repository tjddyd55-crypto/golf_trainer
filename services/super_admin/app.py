# ===== services/super_admin/app.py (총책임자 서비스) =====
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sys
import os
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
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "golf_app_secret_key_change_in_production")

# 데이터베이스 초기화
database.init_db()

# =========================
# 타석 표시 형식 통일 헬퍼 함수
# =========================
def format_bay_display(bay_id=None, bay_name=None):
    """
    bay_id 또는 bay_name을 "XX번 타석" 형식으로 변환
    
    Args:
        bay_id: 타석 ID (예: "01", "02")
        bay_name: 타석 이름 (예: "2번룸", "1타석")
    
    Returns:
        "01번 타석" 형식의 문자열
    """
    # bay_id가 있으면 우선 사용
    if bay_id:
        try:
            # "01" -> 1 -> "01번 타석"
            num = int(bay_id)
            return f"{num:02d}번 타석"
        except (ValueError, TypeError):
            pass
    
    # bay_name에서 숫자 추출
    if bay_name:
        import re
        # 숫자 추출 (예: "2번룸" -> "2", "1타석" -> "1")
        match = re.search(r'(\d+)', str(bay_name))
        if match:
            num = int(match.group(1))
            return f"{num:02d}번 타석"
    
    # 둘 다 없으면 기본값
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
        
        return render_template("super_admin_dashboard.html",
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
        
        # 각 타석의 PC 등록 상태 및 유효성 확인
        cur.execute("""
            SELECT bay_name, pc_name, pc_unique_id, status, usage_start_date, usage_end_date, 
                   approved_at, approved_by, notes
            FROM store_pcs
            WHERE store_name = %s OR store_id = %s
        """, (store_name, store_id))
        pcs = cur.fetchall()
        
        # bay_name에서 타석 번호 추출하여 매칭
        for pc in pcs:
            bay_name = pc.get("bay_name", "")
            match = re.search(r'(\d+)', str(bay_name))
            if match:
                pc_bay_num = int(match.group(1))
                if 1 <= pc_bay_num <= total_bays_count:
                    bay_id = f"{pc_bay_num:02d}"
                    for bay in all_bays:
                        if bay["bay_id"] == bay_id:
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
        
        return render_template("store_bays_detail.html",
                             store=store,
                             bays=all_bays,
                             total_bays_count=total_bays_count,
                             valid_bays_count=valid_bays_count,
                             all_stores=all_stores)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

@app.route("/api/update_bay_settings", methods=["POST"])
@require_role("super_admin")
def update_bay_settings():
    """타석 설정 업데이트 (기간, 상태 등) - PC 미등록 타석도 처리"""
    try:
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
            if bay_exists and bay_exists.get("count", 0) == 0:
                # 타석 생성
                bay_code = database.generate_bay_code(store_id, bay_id, cur)
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
        
        # 승인 완료된 매장
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM stores 
            WHERE status = 'approved' 
            ORDER BY approved_at DESC NULLS LAST, store_id
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
        cur.execute("SELECT * FROM store_pcs ORDER BY registered_at DESC")
        pcs = [dict(row) for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        # 각 PC에 표시용 bay_display 추가
        for pc in pcs:
            pc["bay_display"] = format_bay_display(pc.get("bay_id"), pc.get("bay_name"))
        
        return render_template("manage_all_pcs.html", pcs=pcs)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"오류 발생: {str(e)}", 500

@app.route("/api/approve_pc", methods=["POST"])
@require_role("super_admin")
def approve_pc():
    """PC 승인 (사용 기간 설정 및 타석 정보 설정)"""
    data = request.get_json()
    pc_unique_id = data.get("pc_unique_id")
    store_id = data.get("store_id")  # 매장코드
    bay_id = data.get("bay_id")  # 타석 ID (예: "01", "02")
    usage_start_date = data.get("usage_start_date")  # YYYY-MM-DD 문자열
    usage_end_date = data.get("usage_end_date")  # YYYY-MM-DD 문자열
    approved_date = data.get("approved_date")  # YYYY-MM-DD 문자열 (선택)
    notes = data.get("notes", "")
    
    # 문자열을 DATE로 변환
    from datetime import date
    try:
        start_date = date.fromisoformat(usage_start_date) if usage_start_date else None
        end_date = date.fromisoformat(usage_end_date) if usage_end_date else None
    except (ValueError, TypeError, AttributeError):
        return jsonify({
            "success": False,
            "message": "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)"
        }), 400
    
    # PC 토큰 생성
    conn = database.get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # PC 정보 조회
        cur.execute("SELECT * FROM store_pcs WHERE pc_unique_id = %s", (pc_unique_id,))
        pc_data = cur.fetchone()
        if not pc_data:
            return jsonify({"success": False, "message": "PC를 찾을 수 없습니다."}), 404
        
        pc_data = dict(pc_data)
        mac_address = pc_data.get("mac_address")
        
        # 토큰 생성
        pc_token = database.generate_pc_token(pc_unique_id, mac_address)
        
        # 승인일 설정 (제공된 경우 사용, 없으면 오늘)
        approved_at_value = date.fromisoformat(approved_date) if approved_date else date.today()
        
        # PC 승인 및 사용 기간 설정
        cur.execute("""
            UPDATE store_pcs 
            SET status = 'active',
                store_id = %s,
                bay_id = %s,
                pc_token = %s,
                usage_start_date = %s,
                usage_end_date = %s,
                approved_at = %s,
                approved_by = %s,
                notes = %s
            WHERE pc_unique_id = %s
        """, (store_id, bay_id, pc_token, start_date, end_date, 
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
        import traceback
        traceback.print_exc()
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": f"PC 승인 실패: {str(e)}"}), 400

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
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
