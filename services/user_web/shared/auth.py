# ===== shared/auth.py (권한 관리 미들웨어) =====
from functools import wraps
from flask import session, redirect, url_for

def require_role(*allowed_roles):
    """역할 기반 접근 제어 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("role")
            if user_role not in allowed_roles:
                # 역할별 로그인 페이지로 리다이렉트
                if "super_admin" in allowed_roles:
                    return redirect(url_for("super_admin_login"))
                elif "store_admin" in allowed_roles:
                    return redirect(url_for("store_admin_login"))
                else:
                    return redirect(url_for("user_login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_login(f):
    """로그인 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("user_login"))
        return f(*args, **kwargs)
    return decorated_function
