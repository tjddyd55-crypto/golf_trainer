# ===== build_shot_collector.py (샷 수집 프로그램 빌드 스크립트) =====
"""
샷 수집 프로그램(main.py)을 Windows 실행 파일로 빌드
"""

import PyInstaller.__main__
import os
import shutil

# 빌드 설정
APP_NAME = "shot_collector"
MAIN_SCRIPT = "main.py"
ICON_FILE = None  # 아이콘 파일이 있으면 경로 지정

# 빌드 옵션
build_options = [
    MAIN_SCRIPT,
    "--name", APP_NAME,
    "--onefile",
    "--console",
    "--clean",
    "--noconfirm",
]

# 추가 파일 포함
build_options.extend([
    "--add-data", f"pc_identifier.py;.",
    "--add-data", "config;config",
    "--add-data", "regions;regions",
])

# 아이콘 파일이 있으면 추가
if ICON_FILE and os.path.exists(ICON_FILE):
    build_options.extend(["--icon", ICON_FILE])

# 숨겨진 import 추가
hidden_imports = [
    "cv2",
    "numpy",
    "pytesseract",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "pystray",
    "pyttsx3",
    "pyautogui",
    "requests",
    "openai",
    "psycopg2",
    "psycopg2.extras",
    "pc_identifier",
]

for imp in hidden_imports:
    build_options.extend(["--hidden-import", imp])

# 빌드 실행
print("=" * 60)
print("샷 수집 프로그램 빌드 시작")
print("=" * 60)
print(f"빌드 대상: {MAIN_SCRIPT}")
print(f"출력 파일: {APP_NAME}.exe")
print()

PyInstaller.__main__.run(build_options)

# 빌드 완료 메시지
print()
print("=" * 60)
print("[성공] 빌드 완료!")
print("=" * 60)
print(f"실행 파일 위치: dist/{APP_NAME}.exe")
print()
print("배포 방법:")
print(f"   1. dist/{APP_NAME}.exe 파일을 매장 PC에 복사")
print("   2. Windows 시작 프로그램에 등록하여 자동 실행 설정")
print("   3. PC 등록 및 승인 후 실행 가능")
print("   4. 최소화하면 시스템 트레이로 이동합니다")
print("=" * 60)
