# app.py (project root)
import os
import sys

# 프로젝트 루트를 sys.path에 추가 (Railway 환경 대응)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 디버깅: 경로 확인
print(f"[ROOT APP] Current dir: {current_dir}", flush=True)
print(f"[ROOT APP] sys.path: {sys.path[:3]}", flush=True)

from services.super_admin.app import app
