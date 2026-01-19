# app.py (project root)
import os
import sys

# 프로젝트 루트를 sys.path에 추가 (Railway 환경 대응)
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)

# 여러 가능한 경로를 sys.path에 추가
paths_to_add = [
    current_dir,  # 현재 파일의 디렉토리 (프로젝트 루트)
    os.path.join(current_dir, '..'),  # 상위 디렉토리 (만약 서브디렉토리에서 실행되는 경우)
    os.path.abspath('.'),  # 현재 작업 디렉토리
    '/app',  # Railway의 일반적인 작업 디렉토리
]

for path in paths_to_add:
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path) and abs_path not in sys.path:
        sys.path.insert(0, abs_path)

# 디버깅: 경로 확인
print(f"[ROOT APP] __file__: {current_file}", flush=True)
print(f"[ROOT APP] Current dir: {current_dir}", flush=True)
print(f"[ROOT APP] CWD: {os.getcwd()}", flush=True)
print(f"[ROOT APP] sys.path (first 5): {sys.path[:5]}", flush=True)

# services 디렉토리 존재 확인
services_path = os.path.join(current_dir, 'services')
if not os.path.exists(services_path):
    # 다른 위치에서 찾기 시도
    for path in sys.path:
        test_path = os.path.join(path, 'services')
        if os.path.exists(test_path):
            print(f"[ROOT APP] Found services at: {test_path}", flush=True)
            break
    else:
        print(f"[ROOT APP] ERROR: services directory not found!", flush=True)
        print(f"[ROOT APP] Searched in: {sys.path[:5]}", flush=True)
else:
    print(f"[ROOT APP] services directory found at: {services_path}", flush=True)

from services.super_admin.app import app
