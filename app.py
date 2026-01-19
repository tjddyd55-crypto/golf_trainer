# app.py (project root)
import os
import sys

# 프로젝트 루트를 sys.path에 추가 (Railway 환경 대응)
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
cwd = os.getcwd()

# 여러 가능한 경로를 sys.path에 추가
paths_to_add = [
    current_dir,  # 현재 파일의 디렉토리 (프로젝트 루트)
    cwd,  # 현재 작업 디렉토리
    os.path.join(current_dir, '..'),  # 상위 디렉토리
    os.path.join(current_dir, '../..'),  # 상위의 상위
    '/app',  # Railway의 일반적인 작업 디렉토리
]

for path in paths_to_add:
    try:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and abs_path not in sys.path:
            sys.path.insert(0, abs_path)
    except Exception:
        pass

# 디버깅: 경로 확인
print(f"[ROOT APP] ========== DEBUG START ==========", flush=True)
print(f"[ROOT APP] __file__: {current_file}", flush=True)
print(f"[ROOT APP] Current dir: {current_dir}", flush=True)
print(f"[ROOT APP] CWD: {cwd}", flush=True)
print(f"[ROOT APP] sys.path (first 10): {sys.path[:10]}", flush=True)
# 현재 디렉토리의 파일 목록 확인
try:
    files_in_cwd = os.listdir(cwd)
    print(f"[ROOT APP] Files in CWD: {files_in_cwd[:20]}", flush=True)
except Exception as e:
    print(f"[ROOT APP] Cannot list CWD: {e}", flush=True)
# current_dir의 파일 목록 확인
try:
    files_in_current = os.listdir(current_dir)
    print(f"[ROOT APP] Files in current_dir: {files_in_current[:20]}", flush=True)
except Exception as e:
    print(f"[ROOT APP] Cannot list current_dir: {e}", flush=True)

# services 디렉토리 찾기
services_found = False
services_path = None

# 여러 위치에서 services 찾기 시도
search_paths = [current_dir, cwd] + sys.path[:10]
for path in search_paths:
    try:
        test_path = os.path.join(os.path.abspath(path), 'services')
        if os.path.exists(test_path) and os.path.isdir(test_path):
            services_path = test_path
            services_found = True
            print(f"[ROOT APP] Found services at: {services_path}", flush=True)
            # services의 부모 디렉토리를 sys.path에 추가
            parent = os.path.dirname(services_path)
            if parent not in sys.path:
                sys.path.insert(0, parent)
            break
    except Exception as e:
        continue

if not services_found:
    print(f"[ROOT APP] ERROR: services directory not found!", flush=True)
    print(f"[ROOT APP] Searched in: {search_paths[:10]}", flush=True)
    # 최후의 수단: 현재 디렉토리에서 재귀적으로 찾기
    print(f"[ROOT APP] Starting recursive search from: {os.path.abspath('.')}", flush=True)
    for root, dirs, files in os.walk(os.path.abspath('.'), topdown=True):
        if 'services' in dirs:
            services_path = os.path.join(root, 'services')
            parent = root
            if parent not in sys.path:
                sys.path.insert(0, parent)
            print(f"[ROOT APP] Found services recursively at: {services_path}", flush=True)
            services_found = True
            break
        # 최대 5단계까지만 탐색 (더 깊이 탐색)
        depth = root.replace(os.path.abspath('.'), '').count(os.sep)
        if depth >= 5:
            dirs[:] = []  # 더 깊이 탐색하지 않음
    # 상위 디렉토리에서도 찾기 시도
    if not services_found:
        print(f"[ROOT APP] Trying parent directories...", flush=True)
        for level in range(1, 4):
            parent_dir = os.path.abspath(os.path.join('.', '../' * level))
            test_services = os.path.join(parent_dir, 'services')
            if os.path.exists(test_services) and os.path.isdir(test_services):
                services_path = test_services
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                print(f"[ROOT APP] Found services in parent level {level}: {services_path}", flush=True)
                services_found = True
                break

if not services_found:
    raise ImportError("Cannot find 'services' directory. Check Railway working directory and file structure.")

# 최종 sys.path 확인
print(f"[ROOT APP] Final sys.path (first 5): {sys.path[:5]}", flush=True)

# 동적 import 시도 (여러 방법 시도)
try:
    from services.super_admin.app import app
    print(f"[ROOT APP] Successfully imported app from services.super_admin.app", flush=True)
except ImportError as e:
    print(f"[ROOT APP] Import error: {e}", flush=True)
    # 대안: importlib 사용
    import importlib.util
    super_admin_path = os.path.join(services_path, 'super_admin', 'app.py')
    if os.path.exists(super_admin_path):
        spec = importlib.util.spec_from_file_location("services.super_admin.app", super_admin_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # services 패키지 구조 생성
            import types
            services_module = types.ModuleType('services')
            super_admin_module = types.ModuleType('services.super_admin')
            sys.modules['services'] = services_module
            sys.modules['services.super_admin'] = super_admin_module
            spec.loader.exec_module(module)
            app = module.app
            print(f"[ROOT APP] Successfully loaded app via importlib", flush=True)
        else:
            raise ImportError(f"Cannot load module from {super_admin_path}")
    else:
        raise ImportError(f"super_admin/app.py not found at {super_admin_path}")
