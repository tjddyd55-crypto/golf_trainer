# ===== services/api/app.py (공통 API 서비스) =====
from flask import Flask, request, jsonify
import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

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
# PC 등록 API (register_pc.py에서 사용)
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
def get_coordinates_base_dir():
    """좌표 파일 저장 기본 디렉토리 반환"""
    base_dir = Path(current_dir) / "data" / "coordinates"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

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
        base_dir = get_coordinates_base_dir()
        brand_dir = base_dir / brand
        
        if not brand_dir.exists():
            return jsonify({
                "success": True,
                "files": []
            }), 200
        
        # JSON 파일 목록 조회
        json_files = list(brand_dir.glob("*.json"))
        files = []
        for file_path in sorted(json_files):
            filename = file_path.name
            try:
                # 파일 메타데이터 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    files.append({
                        "filename": filename,
                        "brand": data.get("brand", brand),
                        "resolution": data.get("resolution", ""),
                        "version": data.get("version", 0),
                        "created_at": data.get("created_at", "")
                    })
            except Exception:
                # JSON 파싱 실패 시 파일명만 추가
                files.append({
                    "filename": filename,
                    "brand": brand,
                    "resolution": "",
                    "version": 0,
                    "created_at": ""
                })
        
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
        base_dir = get_coordinates_base_dir()
        brand_dir = base_dir / brand
        file_path = brand_dir / filename
        
        # 보안: 상위 디렉토리 접근 방지
        if not str(file_path.resolve()).startswith(str(base_dir.resolve())):
            return jsonify({
                "success": False,
                "error": "Invalid path"
            }), 400
        
        if not file_path.exists():
            return jsonify({
                "success": False,
                "error": "File not found"
            }), 404
        
        # JSON 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            "success": True,
            "data": data
        }), 200
        
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
        
        # 3. 디렉토리 생성
        base_dir = get_coordinates_base_dir()
        brand_dir = base_dir / brand
        brand_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. 최신 버전 탐색 (자동 증가)
        filename_pattern = f"{brand}_{resolution}_v*.json"
        existing_files = list(brand_dir.glob(filename_pattern))
        
        max_version = 0
        for file_path in existing_files:
            filename = file_path.name
            # 파일명에서 버전 추출 (예: GOLFZON_1920x1080_v3.json -> 3)
            match = re.search(r'_v(\d+)\.json$', filename)
            if match:
                version = int(match.group(1))
                if version > max_version:
                    max_version = version
        
        next_version = max_version + 1
        
        # 5. 파일 저장
        filename = f"{brand}_{resolution}_v{next_version}.json"
        file_path = brand_dir / filename
        
        created_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        file_data = {
            "brand": brand,
            "resolution": resolution,
            "version": next_version,
            "created_at": created_at,
            "regions": regions
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)
        
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
