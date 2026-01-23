# ===== build_register_pc_gui.py (PC 등록 프로그램 GUI 빌드 스크립트) =====
"""
PC 등록 프로그램 GUI 버전을 Windows 실행 파일로 빌드
"""

import PyInstaller.__main__
import os
import shutil

# 빌드 설정
APP_NAME = "register_pc_gui"
MAIN_SCRIPT = "client/pc_register/register_pc_gui.py"
ICON_FILE = None  # 아이콘 파일이 있으면 경로 지정

# 빌드 옵션
build_options = [
    MAIN_SCRIPT,
    "--name", APP_NAME,
    "--onefile",
    "--windowed",  # 콘솔 창 숨김 (GUI 전용)
    "--clean",
    "--noconfirm",
    "--hidden-import", "client.core.pc_identifier",  # pc_identifier 모듈 명시적 포함
    "--hidden-import", "tkinter",  # tkinter 명시적 포함
    "--hidden-import", "requests",  # requests 라이브러리 포함
]

# 아이콘 파일이 있으면 추가
if ICON_FILE and os.path.exists(ICON_FILE):
    build_options.extend(["--icon", ICON_FILE])

# 빌드 실행
print("=" * 60)
print("PC 등록 프로그램 GUI 빌드 시작")
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
print("[INFO] 배포 방법:")
print(f"   1. dist/{APP_NAME}.exe 파일을 매장 PC에 복사")
print("   2. 매장 PC에서 더블클릭하여 실행")
print("   3. 등록 정보 입력 후 등록 요청 클릭")
print("=" * 60)
