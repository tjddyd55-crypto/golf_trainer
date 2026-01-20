# ===== build_calibrate_regions_gui.py (좌표 설정 프로그램 GUI 빌드 스크립트) =====
"""
좌표 설정 프로그램 GUI 버전을 Windows 실행 파일로 빌드
"""

import PyInstaller.__main__
import os
import shutil

# 빌드 설정
APP_NAME = "calibrate_regions_gui"
MAIN_SCRIPT = "client/calibration/calibrate_regions_gui.py"
ICON_FILE = None  # 아이콘 파일이 있으면 경로 지정

# 빌드 옵션
build_options = [
    MAIN_SCRIPT,
    "--name", APP_NAME,
    "--onefile",
    "--windowed",  # 콘솔 창 숨김 (GUI 전용)
    "--clean",
    "--noconfirm",
    "--hidden-import", "cv2",  # OpenCV 명시적 포함
    "--hidden-import", "pyautogui",  # pyautogui 명시적 포함
    "--hidden-import", "numpy",  # numpy 명시적 포함
    "--hidden-import", "tkinter",  # tkinter 명시적 포함
    "--hidden-import", "PIL",  # PIL 명시적 포함 (pyautogui 의존성)
]

# 아이콘 파일이 있으면 추가
if ICON_FILE and os.path.exists(ICON_FILE):
    build_options.extend(["--icon", ICON_FILE])

# 빌드 실행
print("=" * 60)
print("좌표 설정 프로그램 GUI 빌드 시작")
print("=" * 60)
print(f"빌드 대상: {MAIN_SCRIPT}")
print(f"출력 파일: {APP_NAME}.exe")
print()

PyInstaller.__main__.run(build_options)

# 빌드 완료 메시지
print()
print("=" * 60)
print("[OK] 빌드 완료!")
print("=" * 60)
print(f"실행 파일 위치: dist/{APP_NAME}.exe")
print()
print("[INFO] 사용 방법:")
print(f"   1. dist/{APP_NAME}.exe 파일을 실행")
print("   2. 매장 ID 입력 (또는 기본값 test 사용)")
print("   3. 화면 캡처 버튼 클릭")
print("   4. 설정할 항목 선택")
print("   5. 좌표 설정 시작 버튼 클릭")
print("   6. 각 항목의 영역을 드래그하여 선택")
print("   7. 저장 버튼 클릭")
print("=" * 60)
