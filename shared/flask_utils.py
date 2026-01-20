# ===== shared/flask_utils.py (Flask 공통 유틸리티) =====
"""
Flask 애플리케이션 설정 및 공통 유틸리티 함수
모든 서비스에서 공통으로 사용되는 Flask 설정 코드를 모아둡니다.
"""
import os
import sys
from flask import Flask


def setup_shared_path(current_file_path: str) -> None:
    """
    공유 모듈 경로를 sys.path에 추가
    
    Args:
        current_file_path: 현재 파일의 경로 (__file__)
    """
    current_dir = os.path.dirname(os.path.abspath(current_file_path))
    local_shared = os.path.join(current_dir, 'shared')
    
    if os.path.exists(local_shared):
        sys.path.insert(0, current_dir)
    else:
        project_root = os.path.abspath(os.path.join(current_dir, '../../'))
        sys.path.insert(0, project_root)


def get_static_path(current_file_path: str) -> str:
    """
    Static 폴더 경로 찾기 (로컬 우선, 없으면 상위 폴더)
    
    Args:
        current_file_path: 현재 파일의 경로 (__file__)
    
    Returns:
        static 폴더 경로
    """
    current_dir = os.path.dirname(os.path.abspath(current_file_path))
    static_path = os.path.join(current_dir, 'static')
    
    if not os.path.exists(static_path):
        static_path = os.path.join(current_dir, '../../static')
        if not os.path.exists(static_path):
            static_path = 'static'  # 기본값
    
    return static_path


def configure_flask_secret_key(app: Flask) -> None:
    """
    Flask Secret Key 환경 변수 설정 및 검증
    
    Args:
        app: Flask 애플리케이션 인스턴스
    """
    FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
    if not FLASK_SECRET_KEY:
        print("[WARNING] FLASK_SECRET_KEY 환경 변수가 설정되지 않았습니다. 프로덕션에서는 보안 위험이 있습니다.", flush=True)
        FLASK_SECRET_KEY = "golf_app_secret_key_change_in_production"  # 개발용 기본값
    app.secret_key = FLASK_SECRET_KEY


def setup_security_headers(app: Flask) -> None:
    """
    Flask 애플리케이션에 보안 헤더 및 세션 설정 추가
    
    Args:
        app: Flask 애플리케이션 인스턴스
    """
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


def create_flask_app(service_name: str, current_file_path: str, template_folder: str = 'templates') -> Flask:
    """
    Flask 애플리케이션 생성 및 기본 설정
    
    Args:
        service_name: 서비스 이름 (예: 'super_admin', 'user_web', 'store_admin')
        current_file_path: 현재 파일의 경로 (__file__)
        template_folder: 템플릿 폴더 이름 (기본값: 'templates')
    
    Returns:
        설정된 Flask 애플리케이션 인스턴스
    """
    # 공유 모듈 경로 설정
    setup_shared_path(current_file_path)
    
    # Static 폴더 경로 찾기
    static_path = get_static_path(current_file_path)
    
    # Flask 앱 생성
    app = Flask(__name__,
                template_folder=template_folder,
                static_folder=static_path)
    
    # Secret Key 설정
    configure_flask_secret_key(app)
    
    # 보안 헤더 설정
    setup_security_headers(app)
    
    return app
