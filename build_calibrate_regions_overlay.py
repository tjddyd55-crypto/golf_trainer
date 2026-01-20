# ===== build_calibrate_regions_overlay.py (좌표 설정 프로그램 빌드 스크립트) =====
"""
좌표 설정 프로그램(calibrate_regions_overlay.py)을 Windows 실행 파일로 빌드
"""

import PyInstaller.__main__
import os

# 빌드 설정
APP_NAME = "calibrate_regions_overlay"
MAIN_SCRIPT = "client/calibration/calibrate_regions_overlay.py"
ICON_FILE = None  # 아이콘 파일이 있으면 경로 지정

# 빌드 옵션
build_options = [
    MAIN_SCRIPT,
    "--name", APP_NAME,
    "--onefile",
    "--windowed",  # 콘솔 창 없이 실행 (GUI 프로그램)
    "--clean",
    "--noconfirm",
]

# 추가 파일 포함 (regions 폴더는 더 이상 사용하지 않지만, 하위 호환성 유지)
# build_options.extend([
#     "--add-data", "regions;regions",
# ])

# 아이콘 파일이 있으면 추가
if ICON_FILE and os.path.exists(ICON_FILE):
    build_options.extend(["--icon", ICON_FILE])

# 숨겨진 import 추가
hidden_imports = [
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
    "tkinter.simpledialog",
    "requests",
]

for imp in hidden_imports:
    build_options.extend(["--hidden-import", imp])

# 빌드 실행
print("=" * 60)
print("좌표 설정 프로그램 빌드 시작")
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
print("사용 방법:")
print("   1. 게임을 전체화면으로 실행")
print("   2. 좌표 설정 프로그램 실행")
print("   3. 브랜드 선택 (골프존, SG골프, 카카오골프, 브라보, 기타)")
print("   4. 마우스로 숫자 영역 드래그")
print("   5. Enter 키를 눌러 저장")
print("   6. 모든 항목 설정 완료 후 서버 업로드 선택")
print("=" * 60)
