# ===== services/api/app.py (공통 API 서비스) =====
from flask import Flask, request, jsonify
import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

# =========================
# 좌표 파일 저장 (DB 저장)
# =========================
def save_coordinate_file(brand: str, filename: str, payload: dict):
    """좌표 파일 DB 저장"""
    import json
    conn = database.get_db_connection()
    cur = conn.cursor()
    
    try:
        # payload에서 brand, resolution, version 추출
        brand_val = payload.get("brand", brand).upper()
        resolution = payload.get("resolution", "")
        version = payload.get("version", 0)
        
        # JSONB로 저장 (json.dumps 사용)
        payload_json = json.dumps(payload, ensure_ascii=False)
        
        cur.execute("""
            INSERT INTO coordinates (brand, resolution, version, filename, payload)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (brand, resolution, version) 
            DO UPDATE SET filename = EXCLUDED.filename, payload = EXCLUDED.payload
        """, (brand_val, resolution, version, filename, payload_json))
        
        conn.commit()
        return filename
    finally:
        cur.close()
        conn.close()

def list_coordinate_files(brand: str):
    """좌표 파일 목록 조회 (DB에서)"""
    brand = brand.upper()
    conn = database.get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT filename, version, resolution, created_at
            FROM coordinates
            WHERE brand = %s
            ORDER BY version DESC
        """, (brand,))
        
        rows = cur.fetchall()
        
        files = []
        for row in rows:
            filename, version, resolution, created_at = row
            files.append({
                "filename": filename,
                "brand": brand,
                "resolution": resolution,
                "version": version,
                "created_at": created_at.isoformat() if created_at else ""
            })
        
        return files
    finally:
        cur.close()
        conn.close()

def load_coordinate_file(brand: str, filename: str):
    """좌표 파일 로드 (DB에서)"""
    brand = brand.upper()
    conn = database.get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT payload
            FROM coordinates
            WHERE brand = %s AND filename = %s
        """, (brand, filename))
        
        row = cur.fetchone()
        if not row:
            raise FileNotFoundError(f"좌표 파일 없음: {filename}")
        
        # JSONB는 자동으로 dict로 변환됨
        return row[0]
    finally:
        cur.close()
        conn.close()

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

# 테스트 모드 스위치 (기본값: False)
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

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
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "데이터가 없습니다"}), 400
        
        # PC 토큰에서 pc_unique_id 추출 (Authorization 헤더 또는 payload에서)
        pc_unique_id = data.get("pc_unique_id")
        if not pc_unique_id:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                pc_token = auth_header.replace("Bearer ", "")
                pc_data = database.verify_pc_token(pc_token)
                if pc_data:
                    pc_unique_id = pc_data.get("pc_unique_id")
                    data["pc_unique_id"] = pc_unique_id
        
        # store_name은 저장하지 않음 (조회 시 조인)
        if "store_name" in data:
            del data["store_name"]
        
        print("📥 서버 수신 데이터:", data)
        database.save_shot_to_db(data)
        return jsonify({"status": "ok"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================
# 활성 사용자 조회 API (main.py에서 사용)
# =========================
@app.route("/api/active_user", methods=["GET"])
def get_active_user():
    try:
        store_id = request.args.get("store_id")
        bay_id = request.args.get("bay_id")
        
        if not store_id or not bay_id:
            return jsonify({"error": "store_id and bay_id required"}), 400
        
        active_user = database.get_active_user(store_id, bay_id)
        return jsonify(active_user if active_user else {})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =========================
# 세션 삭제 API (main.py에서 사용)
# =========================
@app.route("/api/clear_session", methods=["POST"])
def clear_session():
    try:
        data = request.get_json() or {}
        store_id = data.get("store_id") or request.args.get("store_id")
        bay_id = data.get("bay_id") or request.args.get("bay_id")
        
        if store_id and bay_id:
            deleted = database.clear_active_session(store_id, bay_id)
            return jsonify({"success": True, "deleted": deleted})
        return jsonify({"success": False, "error": "store_id and bay_id required"}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# =========================
# 매장 조회 API (PC 등록 GUI에서 사용)
# =========================
@app.route("/api/get_store", methods=["GET"])
def get_store():
    """매장 정보 조회 API (store_id로 조회)"""
    try:
        store_id = request.args.get("store_id", "").strip().upper()
        
        if not store_id:
            return jsonify({
                "success": False,
                "error": "store_id is required"
            }), 400
        
        store = database.get_store_by_id(store_id)
        
        if not store:
            return jsonify({
                "success": False,
                "error": "매장을 찾을 수 없습니다."
            }), 404
        
        # 필요한 정보만 반환 (매장명, 사업자등록번호)
        return jsonify({
            "success": True,
            "store_id": store.get("store_id"),
            "store_name": store.get("store_name"),
            "business_number": store.get("business_number")
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# 매장 좌석 상태 조회 API (PC 등록 프로그램에서 사용)
# =========================
@app.route("/api/stores/<store_id>/bays", methods=["GET"])
def get_store_bays(store_id):
    """
    매장 좌석 상태 조회 API
    
    Response:
    {
      "store_id": "A",
      "bays_count": 10,
      "bays": [
        {"bay_number": 1, "bay_name": "1번룸", "assigned": true},
        {"bay_number": 2, "bay_name": null, "assigned": false},
        ...
      ]
    }
    """
    try:
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 매장 정보 조회
        cur.execute("SELECT store_id, store_name, bays_count FROM stores WHERE store_id = %s", (store_id,))
        store = cur.fetchone()
        
        if not store:
            cur.close()
            conn.close()
            return jsonify({"error": "매장을 찾을 수 없습니다."}), 404
        
        bays_count = store.get("bays_count", 0) or 0
        
        # bays 테이블에서 할당된 타석 조회
        cur.execute("""
            SELECT 
                b.bay_number,
                b.bay_name,
                b.assigned_pc_unique_id,
                sp.pc_unique_id as pc_connected
            FROM bays b
            LEFT JOIN store_pcs sp ON sp.store_id = b.store_id 
                AND sp.bay_id = CAST(b.bay_number AS TEXT)
                AND sp.status = 'active'
            WHERE b.store_id = %s
            ORDER BY b.bay_number
        """, (store_id,))
        
        assigned_bays = {row.get("bay_number"): row for row in cur.fetchall()}
        
        # store_pcs에서도 할당 상태 확인 (bay_id가 숫자인 경우 bay_number로 간주)
        cur.execute("""
            SELECT DISTINCT
                CAST(bay_id AS INTEGER) as bay_number,
                bay_name
            FROM store_pcs
            WHERE store_id = %s
              AND status = 'active'
              AND bay_id IS NOT NULL
              AND bay_id ~ '^[0-9]+$'
        """, (store_id,))
        
        pc_assigned_bays = {row.get("bay_number"): row for row in cur.fetchall()}
        
        # 모든 타석 목록 생성 (1..bays_count)
        bays = []
        for bay_num in range(1, bays_count + 1):
            bay_info = assigned_bays.get(bay_num) or pc_assigned_bays.get(bay_num)
            
            # assigned=true 기준:
            # 1. bays에 해당 bay_number가 존재하고 assigned_pc_unique_id가 있거나
            # 2. store_pcs에서 해당 bay_id(숫자)가 연결되어 있는 경우
            assigned = False
            bay_name = None
            
            if bay_info:
                assigned = bool(bay_info.get("assigned_pc_unique_id") or bay_info.get("pc_connected"))
                bay_name = bay_info.get("bay_name")
            
            bays.append({
                "bay_number": bay_num,
                "bay_name": bay_name,
                "assigned": assigned
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "store_id": store_id,
            "bays_count": bays_count,
            "bays": bays
        })
        
    except Exception as e:
        print(f"[ERROR] get_store_bays 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =========================
# PC 등록 API (새로운 방식: bay_number 기반)
# =========================
@app.route("/api/pcs/register", methods=["POST"])
def register_pc_new():
    """
    PC 등록 API (bay_number 기반)
    
    Request:
    {
      "store_id": "A",
      "pc_unique_id": "xxx",
      "bay_number": 3,
      "bay_name": "VIP룸"  // optional
    }
    
    Response:
    {
      "ok": true,
      "store_id": "A",
      "bay_id": "...",
      "bay_number": 3,
      "bay_name": "VIP룸"
    }
    """
    try:
        data = request.get_json()
        store_id = data.get("store_id")
        pc_unique_id = data.get("pc_unique_id")
        bay_number = data.get("bay_number")
        bay_name = data.get("bay_name")
        
        # ✅ 로그: 요청 payload 확인
        print(f"[PC 등록 API] 요청 받음: store_id={store_id}, pc_unique_id={pc_unique_id}, bay_number={bay_number}, bay_name={bay_name}")
        
        if not store_id or not pc_unique_id or bay_number is None:
            return jsonify({
                "ok": False,
                "error": "store_id, pc_unique_id, bay_number are required"
            }), 400
        
        # bay_number 타입 확인 및 변환
        try:
            bay_number = int(bay_number)
        except (ValueError, TypeError):
            return jsonify({
                "ok": False,
                "error": f"bay_number는 숫자여야 합니다. (받은 값: {bay_number})"
            }), 400
        
        print(f"[PC 등록 API] bay_number 검증 완료: {bay_number} (정수)")
        
        # bay_number 범위 확인
        from psycopg2.extras import RealDictCursor
        conn = database.get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # store_id로 store_name 조회 (필수)
        cur.execute("SELECT store_name, bays_count FROM stores WHERE store_id = %s", (store_id,))
        store = cur.fetchone()
        
        if not store:
            cur.close()
            conn.close()
            print(f"[PC 등록 API] 매장 조회 실패: store_id={store_id} (매장 없음)")
            return jsonify({"ok": False, "error": "매장을 찾을 수 없습니다."}), 404
        
        store_name = store.get("store_name")
        bays_count = store.get("bays_count", 0) or 0
        
        # store_name 명시적 검증 (None, 빈 문자열, 공백 모두 체크)
        if not store_name or not str(store_name).strip():
            cur.close()
            conn.close()
            print(f"[PC 등록 API] store_name 검증 실패: store_id={store_id}, store_name={store_name}")
            return jsonify({"ok": False, "error": "매장 정보가 올바르지 않습니다. (store_name 없음)"}), 400
        
        # store_name 문자열로 확실히 변환
        store_name = str(store_name).strip()
        
        print(f"[PC 등록 API] 매장 조회 완료: store_id={store_id}, store_name={store_name}, bays_count={bays_count}")
        
        if bay_number < 1 or bay_number > bays_count:
            cur.close()
            conn.close()
            return jsonify({
                "ok": False,
                "error": f"bay_number는 1부터 {bays_count} 사이여야 합니다."
            }), 400
        
        # ✅ 동일 PC 재등록 확인 (pc_unique_id 기준)
        cur.execute("""
            SELECT store_id, bay_number, bay_name, status
            FROM store_pcs
            WHERE pc_unique_id = %s
            LIMIT 1
        """, (pc_unique_id,))
        
        existing_pc = cur.fetchone()
        if existing_pc:
            existing_store_id = existing_pc.get("store_id")
            existing_bay_number = existing_pc.get("bay_number")
            existing_bay_name = existing_pc.get("bay_name")
            existing_status = existing_pc.get("status")
            
            # 동일 PC가 이미 등록되어 있으면 안내 메시지 반환
            bay_display = existing_bay_name if existing_bay_name else f"{existing_bay_number}번 타석(룸)"
            cur.close()
            conn.close()
            print(f"[PC 등록 API] 동일 PC 재등록 시도: pc_unique_id={pc_unique_id}, 기존 타석={bay_display}")
            return jsonify({
                "ok": False,
                "error": f"이미 등록된 PC입니다. 현재 {bay_display}에 등록되어 있습니다. (상태: {existing_status})"
            }), 409
        
        # ✅ 중복 확인 1: bays 테이블에서 bay_number 중복 체크
        cur.execute("""
            SELECT 1
            FROM bays
            WHERE store_id = %s
              AND bay_number = %s
            LIMIT 1
        """, (store_id, bay_number))
        
        if cur.fetchone():
            cur.close()
            conn.close()
            print(f"[PC 등록 API] 중복 발견 (bays 테이블): store_id={store_id}, bay_number={bay_number}")
            return jsonify({
                "ok": False,
                "error": f"타석 번호 {bay_number}는 이미 할당되어 있습니다."
            }), 409
        
        # ✅ 중복 확인 2: store_pcs 테이블에서 bay_number 중복 체크 (중요!)
        cur.execute("""
            SELECT 1
            FROM store_pcs
            WHERE store_id = %s
              AND bay_number = %s
              AND status IN ('pending', 'active')
            LIMIT 1
        """, (store_id, bay_number))
        
        if cur.fetchone():
            cur.close()
            conn.close()
            print(f"[PC 등록 API] 중복 발견 (store_pcs 테이블): store_id={store_id}, bay_number={bay_number}")
            return jsonify({
                "ok": False,
                "error": f"타석 번호 {bay_number}는 이미 할당되어 있습니다."
            }), 409
        
        print(f"[PC 등록 API] 중복 체크 완료: store_id={store_id}, bay_number={bay_number} (중복 없음)")
        
        # bay_id 생성 (내부 키로 사용, UUID 기반)
        import uuid
        bay_id = str(uuid.uuid4())[:8]  # 간단한 ID
        
        # bays 테이블에 생성 또는 업데이트
        cur.execute("""
            INSERT INTO bays (store_id, bay_id, bay_number, bay_name, status, assigned_pc_unique_id)
            VALUES (%s, %s, %s, %s, 'READY', %s)
            ON CONFLICT (store_id, bay_id) DO UPDATE
            SET bay_number = EXCLUDED.bay_number,
                bay_name = COALESCE(EXCLUDED.bay_name, bays.bay_name),
                assigned_pc_unique_id = EXCLUDED.assigned_pc_unique_id
        """, (store_id, bay_id, bay_number, bay_name, pc_unique_id))
        
        # store_pcs INSERT 또는 UPDATE (PC가 없으면 INSERT, 있으면 UPDATE)
        # status는 'PENDING'으로 설정 (관리자 승인 대기)
        # bay_id는 UUID 문자열로 저장 (bay_number는 별도 컬럼)
        # ✅ store_name 필수 포함 (NOT NULL 제약조건)
        
        # INSERT 직전 store_name 최종 검증
        if not store_name or not str(store_name).strip():
            cur.close()
            conn.close()
            print(f"[PC 등록 API] INSERT 직전 store_name 검증 실패: store_name={store_name}")
            return jsonify({"ok": False, "error": "매장 정보가 올바르지 않습니다. (store_name 없음)"}), 500
        
        print(f"[PC 등록 API] store_pcs INSERT 시작: store_id={store_id}, store_name={store_name}, bay_id={bay_id}, bay_number={bay_number}, pc_unique_id={pc_unique_id}")
        
        try:
            cur.execute("""
                INSERT INTO store_pcs (
                    store_id, store_name, bay_id, bay_name, pc_unique_id, 
                    status, registered_at, bay_number
                )
                VALUES (%s, %s, %s, %s, %s, 'pending', CURRENT_TIMESTAMP, %s)
                ON CONFLICT (pc_unique_id) DO UPDATE SET
                    store_id = EXCLUDED.store_id,
                    store_name = COALESCE(EXCLUDED.store_name, store_pcs.store_name),
                    bay_id = EXCLUDED.bay_id,
                    bay_name = COALESCE(EXCLUDED.bay_name, store_pcs.bay_name),
                    bay_number = EXCLUDED.bay_number,
                    status = CASE 
                        WHEN store_pcs.status = 'active' THEN 'active'  -- 이미 승인된 경우 유지
                        ELSE 'pending'  -- 새 등록이면 대기 상태
                    END
            """, (store_id, store_name, bay_id, bay_name, pc_unique_id, bay_number))
            
            print(f"[PC 등록 API] store_pcs INSERT 완료")
        except Exception as e:
            print(f"[PC 등록 API] store_pcs INSERT 오류: {e}")
            print(f"[PC 등록 API] INSERT 시도 값: store_id={store_id}, store_name={store_name}, bay_id={bay_id}, bay_number={bay_number}")
            conn.rollback()
            cur.close()
            conn.close()
            raise
        
        # DB commit 확인 후 응답
        conn.commit()
        
        # commit 성공 확인
        cur.execute("SELECT status FROM store_pcs WHERE pc_unique_id = %s", (pc_unique_id,))
        saved_pc = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not saved_pc:
            return jsonify({
                "ok": False,
                "error": "PC 등록 저장에 실패했습니다."
            }), 500
        
        return jsonify({
            "ok": True,
            "store_id": store_id,
            "bay_id": bay_id,
            "bay_number": bay_number,
            "bay_name": bay_name
        })
        
    except Exception as e:
        print(f"[ERROR] register_pc_new 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

# =========================
# PC 등록 API (기존 방식: 등록 키 기반)
# =========================
@app.route("/api/register_pc", methods=["POST"])
@app.route("/pc/register", methods=["POST"])
def register_pc():
    """PC 등록 API (등록 키 검증 후 토큰 발급)"""
    try:
        data = request.get_json()
        
        registration_key = data.get("registration_key")
        store_id = data.get("store_id")
        store_name = data.get("store_name")
        bay_name = data.get("bay_name")
        pc_name = data.get("pc_name")
        pc_info = data.get("pc_info")
        
        # 필수 파라미터 확인
        if not registration_key:
            return jsonify({
                "success": False,
                "error": "registration_key is required"
            }), 400
        
        if not store_name or not bay_name or not pc_name or not pc_info:
            return jsonify({
                "success": False,
                "error": "store_name, bay_name, pc_name, pc_info are required"
            }), 400
        
        # 필수 정보 확인 (MAC Address, UUID)
        mac_address = pc_info.get("mac_address")
        pc_uuid = pc_info.get("system_uuid") or pc_info.get("machine_guid")
        
        if not mac_address:
            return jsonify({
                "success": False,
                "error": "MAC Address is required"
            }), 400
        
        if not pc_uuid:
            return jsonify({
                "success": False,
                "error": "PC UUID is required"
            }), 400
        
        # 등록 코드로 PC 등록 및 토큰 발급
        pc_data, error = database.register_pc_with_code(
            registration_key, store_name, bay_name, pc_name, pc_info, store_id=store_id
        )
        
        if pc_data:
            return jsonify({
                "success": True,
                "message": "PC 등록이 완료되었습니다.",
                "pc_token": pc_data.get("pc_token"),
                "status": "active"
            })
        else:
            return jsonify({
                "success": False,
                "error": error or "PC 등록에 실패했습니다."
            }), 400
            
    except Exception as e:
        print(f"PC 등록 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# PC 인증 API (main.py에서 사용)
# =========================
@app.route("/api/verify_pc", methods=["POST"])
def verify_pc():
    """PC 토큰 검증 API"""
    try:
        data = request.get_json() or {}
        pc_token = data.get("pc_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not pc_token:
            return jsonify({
                "success": False,
                "error": "PC token is required"
            }), 401
        
        # 토큰 검증
        pc_data = database.verify_pc_token(pc_token)
        
        if pc_data:
            return jsonify({
                "success": True,
                "pc": {
                    "store_id": pc_data.get("store_id"),
                    "bay_id": pc_data.get("bay_id"),
                    "store_name": pc_data.get("store_name"),
                    "bay_name": pc_data.get("bay_name"),
                    "pc_name": pc_data.get("pc_name")
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "Invalid or inactive PC token"
            }), 401
            
    except Exception as e:
        print(f"PC 인증 오류: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# PC 등록 상태 확인 API (샷 수집 프로그램에서 사용)
# =========================
@app.route("/api/check_pc_status", methods=["POST"])
def check_pc_status():
    """PC 실행 허용 여부 확인 (타석 기준만)"""
    try:
        # =========================
        # 🔧 TEST MODE (강제 통과)
        # =========================
        if TEST_MODE:
            return jsonify({
                "allowed": True,
                "reason": "TEST_MODE_FORCE_ALLOW",
                "status": "ACTIVE"
            }), 200
        
        # =========================
        # 기존 로직 (그대로 유지)
        # =========================
        data = request.get_json() or {}
        pc_unique_id = data.get("pc_unique_id")
        
        if not pc_unique_id:
            return jsonify({
                "allowed": False,
                "reason": "MISSING_PC_ID"
            }), 400
        
        pc_data = database.get_store_pc_by_unique_id(pc_unique_id)
        if not pc_data:
            return jsonify({
                "allowed": False,
                "reason": "NOT_REGISTERED"
            })
        
        # PC 상태 체크
        if pc_data.get("status") != "active":
            return jsonify({
                "allowed": False,
                "reason": "INACTIVE",
                "status": pc_data.get("status")
            })
        
        # 사용 기간 체크 (DATE 타입 직접 비교)
        from datetime import date
        today = date.today()
        usage_end = pc_data.get("usage_end_date")
        
        if usage_end:
            # DATE 타입이면 date 객체로 직접 비교
            if isinstance(usage_end, date):
                if today > usage_end:
                    return jsonify({
                        "allowed": False,
                        "reason": "EXPIRED",
                        "expires_at": usage_end.isoformat()
                    })
            else:
                # 혼용 대비 (마이그레이션 중)
                try:
                    usage_end_date = date.fromisoformat(str(usage_end))
                    if today > usage_end_date:
                        return jsonify({
                            "allowed": False,
                            "reason": "EXPIRED",
                            "expires_at": usage_end_date.isoformat()
                        })
                except (ValueError, AttributeError):
                    # 변환 실패 시 차단
                    return jsonify({
                        "allowed": False,
                        "reason": "INVALID_DATE"
                    })
        
        # 허용
        expires_at_str = usage_end.isoformat() if usage_end else None
        return jsonify({
            "allowed": True,
            "status": "active",
            "expires_at": expires_at_str,
            "pc_token": pc_data.get("pc_token")
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "allowed": False,
            "reason": "ERROR",
            "error": str(e)
        }), 500

# =========================
# 관리자 API: 등록 코드 생성 (golf-super-admin에서 호출)
# =========================
def verify_admin_credentials(username, password):
    """슈퍼 관리자 인증"""
    super_admin_username = os.environ.get("SUPER_ADMIN_USERNAME", "admin")
    super_admin_password = os.environ.get("SUPER_ADMIN_PASSWORD", "endolpin0!")
    return username == super_admin_username and password == super_admin_password

@app.route("/api/admin/pc-registration-codes", methods=["POST"])
def create_registration_code():
    """PC 등록 코드 생성 API (슈퍼 관리자 전용)"""
    try:
        # 인증 정보 확인
        auth_header = request.headers.get("Authorization", "")
        data = request.get_json() or {}
        
        # Authorization 헤더에서 인증 정보 추출 (Basic 또는 Bearer)
        username = None
        password = None
        
        if auth_header.startswith("Basic "):
            import base64
            try:
                credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = credentials.split(":", 1)
            except Exception:
                pass
        elif auth_header.startswith("Bearer "):
            # Bearer 토큰 방식은 나중에 구현 가능
            pass
        
        # 또는 JSON body에서 인증 정보 받기
        if not username:
            username = data.get("username") or request.headers.get("X-Admin-Username")
            password = data.get("password") or request.headers.get("X-Admin-Password")
        
        # 인증 검증
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "인증 정보가 필요합니다. (username, password)"
            }), 401
        
        if not verify_admin_credentials(username, password):
            return jsonify({
                "success": False,
                "error": "인증 실패"
            }), 401
        
        # 등록 코드 생성
        notes = data.get("notes", "")
        code_data = database.create_registration_code(
            issued_by=username,
            notes=notes
        )
        
        if code_data:
            return jsonify({
                "success": True,
                "registration_code": code_data.get("code"),
                "registration_key": code_data.get("code"),  # 하위 호환성
                "status": code_data.get("status"),
                "message": "등록 코드가 생성되었습니다. 기존 코드는 자동으로 폐기되었습니다."
            })
        else:
            return jsonify({
                "success": False,
                "error": "등록 코드 생성에 실패했습니다."
            }), 500
            
    except Exception as e:
        print(f"등록 코드 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/admin/pc-registration-codes", methods=["GET"])
def get_registration_codes():
    """등록 코드 목록 조회 API (슈퍼 관리자 전용)"""
    try:
        # 인증 정보 확인
        auth_header = request.headers.get("Authorization", "")
        username = request.args.get("username") or request.headers.get("X-Admin-Username")
        password = request.args.get("password") or request.headers.get("X-Admin-Password")
        
        if auth_header.startswith("Basic "):
            import base64
            try:
                credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = credentials.split(":", 1)
            except Exception:
                pass
        
        # 인증 검증
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "인증 정보가 필요합니다. (username, password)"
            }), 401
        
        if not verify_admin_credentials(username, password):
            return jsonify({
                "success": False,
                "error": "인증 실패"
            }), 401
        
        # 등록 코드 목록 조회
        codes = database.get_all_registration_codes()
        return jsonify({
            "success": True,
            "codes": codes,
            "keys": codes  # 하위 호환성
        })
            
    except Exception as e:
        print(f"등록 코드 조회 오류: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# 임시: 테스트용 등록 코드 생성 (빠른 생성용)
# =========================
@app.route("/api/test/create-code", methods=["GET", "POST"])
def test_create_code():
    """테스트용 등록 코드 생성 (인증 없음 - 테스트 전용)"""
    try:
        code_data = database.create_registration_code(
            issued_by="test_api",
            notes="테스트용 등록 코드 (API 생성)"
        )
        
        if code_data:
            return jsonify({
                "success": True,
                "registration_code": code_data.get("code"),
                "message": "등록 코드가 생성되었습니다."
            })
        else:
            return jsonify({
                "success": False,
                "error": "등록 코드 생성 실패"
            }), 500
            
    except Exception as e:
        print(f"등록 코드 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# 좌표 관리 API
# =========================
def extract_auth_from_header():
    """Authorization 헤더에서 인증 정보 추출"""
    auth_header = request.headers.get("Authorization", "")
    username = None
    password = None
    
    if auth_header.startswith("Basic "):
        import base64
        try:
            credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = credentials.split(":", 1)
        except Exception:
            pass
    
    return username, password

@app.route("/api/coordinates/<brand>", methods=["GET"])
def list_coordinates(brand):
    """브랜드별 좌표 파일 목록 조회 API"""
    try:
        brand = brand.upper().strip()
        files = list_coordinate_files(brand)
        
        return jsonify({
            "success": True,
            "files": files
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route("/api/coordinates/<brand>/<filename>", methods=["GET"])
def download_coordinates(brand, filename):
    """좌표 파일 다운로드 API"""
    try:
        brand = brand.upper().strip()
        data = load_coordinate_file(brand, filename)
        
        return jsonify({
            "success": True,
            "data": data
        }), 200
        
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "File not found"
        }), 404
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@app.route("/api/coordinates/upload", methods=["POST"])
def upload_coordinates():
    """좌표 파일 업로드 API (슈퍼 관리자 전용)"""
    try:
        # 1. 인증 확인
        username, password = extract_auth_from_header()
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401
        
        if not verify_admin_credentials(username, password):
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401
        
        # 2. 입력값 검증
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        brand = data.get("brand", "").strip().upper()
        resolution = data.get("resolution", "").strip()
        regions = data.get("regions")
        
        if not brand:
            return jsonify({
                "success": False,
                "error": "brand is required"
            }), 400
        
        if not resolution:
            return jsonify({
                "success": False,
                "error": "resolution is required"
            }), 400
        
        # resolution 형식 검증 (예: "1920x1080")
        if not re.match(r'^\d+x\d+$', resolution):
            return jsonify({
                "success": False,
                "error": "Invalid resolution format. Expected format: WIDTHxHEIGHT (e.g., 1920x1080)"
            }), 400
        
        if not regions or not isinstance(regions, dict) or len(regions) == 0:
            return jsonify({
                "success": False,
                "error": "regions is required and must be a non-empty object"
            }), 400
        
        # 3. 최신 버전 탐색 (자동 증가) - DB에서
        conn = database.get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT MAX(version) as max_version
                FROM coordinates
                WHERE brand = %s AND resolution = %s
            """, (brand, resolution))
            row = cur.fetchone()
            max_version = row[0] if row and row[0] else 0
            next_version = max_version + 1
        finally:
            cur.close()
            conn.close()
        
        # 4. 파일 저장 (DB)
        filename = f"{brand}_{resolution}_v{next_version}.json"
        
        created_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        file_data = {
            "brand": brand,
            "resolution": resolution,
            "version": next_version,
            "created_at": created_at,
            "regions": regions
        }
        
        save_coordinate_file(brand, filename, file_data)
        
        # 6. 성공 응답
        return jsonify({
            "success": True,
            "filename": filename,
            "version": next_version,
            "created_at": created_at
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    app.run(host="0.0.0.0", port=port, debug=True)
