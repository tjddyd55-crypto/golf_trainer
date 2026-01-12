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

app = Flask(__name__, 
            template_folder='templates',
            static_folder='../../static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "golf_app_secret_key_change_in_production")

# 데이터베이스 초기화
database.init_db()

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
        super_admin_password = os.environ.get("SUPER_ADMIN_PASSWORD", "admin123")
        
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
    # 모든 매장 조회
    from psycopg2.extras import RealDictCursor
    conn = database.get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM stores ORDER BY requested_at DESC NULLS LAST, store_id")
    stores = [dict(row) for row in cur.fetchall()]
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

# =========================
# 매장 관리
# =========================
@app.route("/stores")
@require_role("super_admin")
def manage_stores():
    from psycopg2.extras import RealDictCursor
    conn = database.get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM stores ORDER BY requested_at DESC NULLS LAST, store_id")
    stores = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    return render_template("manage_stores.html", stores=stores)

# =========================
# 매장 등록 요청 승인
# =========================
@app.route("/store-requests")
@require_role("super_admin")
def store_requests():
    """승인 대기 중인 매장 등록 요청 목록"""
    pending_stores = database.get_pending_stores()
    return render_template("store_requests.html", stores=pending_stores)

@app.route("/api/approve_store", methods=["POST"])
@require_role("super_admin")
def approve_store():
    """매장 승인"""
    data = request.get_json()
    store_id = data.get("store_id")
    approved_by = session.get("user_id", "super_admin")
    
    if not store_id:
        return jsonify({"success": False, "message": "store_id 필요"}), 400
    
    if database.approve_store(store_id, approved_by):
        return jsonify({"success": True, "message": "매장이 승인되었습니다."})
    else:
        return jsonify({"success": False, "message": "매장 승인 실패"}), 500

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

# =========================
# 결제 관리
# =========================
@app.route("/payments")
@require_role("super_admin")
def manage_payments():
    from psycopg2.extras import RealDictCursor
    conn = database.get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM payments ORDER BY payment_date DESC LIMIT 100")
    payments = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    return render_template("manage_payments.html", payments=payments)

# =========================
# 사용기간 관리
# =========================
@app.route("/subscriptions")
@require_role("super_admin")
def manage_subscriptions():
    from psycopg2.extras import RealDictCursor
    conn = database.get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM subscriptions ORDER BY end_date DESC")
    subscriptions = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    return render_template("manage_subscriptions.html", subscriptions=subscriptions)

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
    """전체 매장 PC 관리"""
    pcs = database.get_all_store_pcs()
    return render_template("manage_all_pcs.html", pcs=pcs)

@app.route("/api/approve_pc", methods=["POST"])
@require_role("super_admin")
def approve_pc():
    """PC 승인 및 토큰 발급"""
    data = request.get_json()
    pc_unique_id = data.get("pc_unique_id")
    store_id = data.get("store_id")
    bay_id = data.get("bay_id")
    approved_by = session.get("user_id", "super_admin")
    usage_start_date = data.get("usage_start_date")
    usage_end_date = data.get("usage_end_date")
    notes = data.get("notes", "")
    
    if not pc_unique_id or not store_id or not bay_id:
        return jsonify({"success": False, "message": "pc_unique_id, store_id, bay_id are required"}), 400
    
    # PC 승인 및 토큰 발급
    pc_data = database.approve_pc(pc_unique_id, store_id, bay_id, approved_by)
    
    if pc_data:
        # 사용 기간 업데이트 (선택사항)
        if usage_start_date or usage_end_date or notes:
            conn = database.get_db_connection()
            cur = conn.cursor()
            if usage_start_date:
                cur.execute("UPDATE store_pcs SET usage_start_date = %s WHERE pc_unique_id = %s", 
                           (usage_start_date, pc_unique_id))
            if usage_end_date:
                cur.execute("UPDATE store_pcs SET usage_end_date = %s WHERE pc_unique_id = %s", 
                           (usage_end_date, pc_unique_id))
            if notes:
                cur.execute("UPDATE store_pcs SET notes = %s WHERE pc_unique_id = %s", 
                           (notes, pc_unique_id))
            conn.commit()
            cur.close()
            conn.close()
        
        return jsonify({
            "success": True, 
            "message": "PC 승인 완료",
            "pc_token": pc_data.get("pc_token"),
            "pc": pc_data
        })
    else:
        return jsonify({"success": False, "message": "PC 승인 실패"}), 400

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
    super_admin_password = os.environ.get("SUPER_ADMIN_PASSWORD", "admin123")
    
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
    super_admin_password = os.environ.get("SUPER_ADMIN_PASSWORD", "admin123")
    
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
