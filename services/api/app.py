# ===== services/api/app.py (공통 API 서비스) =====
from flask import Flask, request, jsonify
import sys
import os

# 공유 모듈 경로 추가
# Railway에서 Root Directory가 services/api일 때를 대비
current_dir = os.path.dirname(os.path.abspath(__file__))
# 같은 디렉토리의 shared 폴더 우선 확인
local_shared = os.path.join(current_dir, 'shared')
if os.path.exists(local_shared):
    sys.path.insert(0, current_dir)
else:
    # 루트의 shared 폴더 확인
    project_root = os.path.abspath(os.path.join(current_dir, '../../'))
    sys.path.insert(0, project_root)
from shared import database

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "golf_app_secret_key_change_in_production")

# 데이터베이스 초기화
database.init_db()

# =========================
# 헬스 체크
# =========================
@app.route("/api/health", methods=["GET"])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({"status": "ok", "service": "api"})

# =========================
# 샷 데이터 저장 API (main.py에서 사용)
# =========================
@app.route("/api/save_shot", methods=["POST"])
def save_shot():
    data = request.json
    print("📥 서버 수신 데이터:", data)
    database.save_shot_to_db(data)
    return jsonify({"status": "ok"})

# =========================
# 활성 사용자 조회 API (main.py에서 사용)
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
# 세션 삭제 API (main.py에서 사용)
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
# PC 등록 API (register_pc.py에서 사용)
# =========================
@app.route("/api/register_pc", methods=["POST"])
def register_pc():
    """매장 PC 등록 API"""
    try:
        data = request.get_json()
        
        store_name = data.get("store_name")
        bay_name = data.get("bay_name")
        pc_name = data.get("pc_name")
        pc_info = data.get("pc_info")
        
        if not store_name or not bay_name or not pc_name or not pc_info:
            return jsonify({
                "success": False,
                "error": "store_name, bay_name, pc_name, pc_info are required"
            }), 400
        
        # 데이터베이스에 PC 등록
        success = database.register_store_pc(store_name, bay_name, pc_name, pc_info)
        
        if success:
            return jsonify({
                "success": True,
                "message": "PC 등록 요청이 접수되었습니다. 슈퍼 관리자의 승인을 기다려주세요."
            })
        else:
            return jsonify({
                "success": False,
                "error": "PC 등록에 실패했습니다."
            }), 500
            
    except Exception as e:
        print(f"PC 등록 오류: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    app.run(host="0.0.0.0", port=port, debug=True)
