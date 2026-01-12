# ===== build_register_pc.py (PC 등록 프로그램 빌드 스크립트) =====
"""
PC 등록 프로그램을 Windows 실행 파일로 빌드
"""

import PyInstaller.__main__
import os
import shutil

# 빌드 설정
APP_NAME = "register_pc"
MAIN_SCRIPT = "register_pc.py"
ICON_FILE = None  # 아이콘 파일이 있으면 경로 지정

# 빌드 옵션
build_options = [
    MAIN_SCRIPT,
    "--name", APP_NAME,
    "--onefile",
    "--console",
    "--clean",
    "--noconfirm",
    "--hidden-import", "pc_identifier",  # pc_identifier 모듈 명시적 포함
]

# 아이콘 파일이 있으면 추가
if ICON_FILE and os.path.exists(ICON_FILE):
    build_options.extend(["--icon", ICON_FILE])

# 빌드 실행
print("=" * 60)
print("PC 등록 프로그램 빌드 시작")
print("=" * 60)
print(f"빌드 대상: {MAIN_SCRIPT}")
print(f"출력 파일: {APP_NAME}.exe")
print()

PyInstaller.__main__.run(build_options)

# 빌드 완료 메시지
print()
print("=" * 60)
print("✅ 빌드 완료!")
print("=" * 60)
print(f"실행 파일 위치: dist/{APP_NAME}.exe")
print()
print("💡 배포 방법:")
print(f"   1. dist/{APP_NAME}.exe 파일을 매장 PC에 복사")
print("   2. 매장 PC에서 실행하여 등록 정보 입력")
print("   3. 슈퍼 관리자가 승인하면 사용 가능")
print("=" * 60)
