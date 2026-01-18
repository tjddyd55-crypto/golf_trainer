# ===== build_shot_collector_gui.py (샷 수집 GUI 프로그램 빌드 스크립트) =====
"""
샷 수집 GUI 프로그램(shot_collector_gui.py)을 Windows 실행 파일로 빌드
"""
import PyInstaller.__main__
import os
import shutil

# 빌드 설정
APP_NAME = "shot_collector_gui"
MAIN_SCRIPT = "client/app/collector/shot_collector_gui.py"
ICON_FILE = None  # 아이콘 파일이 있으면 경로 지정

# 빌드 옵션
build_options = [
    MAIN_SCRIPT,
    "--name", APP_NAME,
    "--onefile",
    "--windowed",  # 콘솔 창 없음
    "--clean",
    "--noconfirm",
]

# 추가 파일 포함 (기준: golf_trainer/config/criteria.json)
build_options.extend([
    "--add-data", "client/core/pc_identifier.py;client/core",
    # 프로젝트 루트의 config/criteria.json을 번들링 (실행 시 실행 경로로 복사됨)
    "--add-data", "config/criteria.json;config/criteria.json",
    "--add-data", "client/app/collector/config;client/app/collector/config",
    "--add-data", "client/app/collector/regions;client/app/collector/regions",
])

# 아이콘 파일이 있으면 추가
if ICON_FILE and os.path.exists(ICON_FILE):
    build_options.extend(["--icon", ICON_FILE])

# 숨겨진 import 추가
hidden_imports = [
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
    "requests",
    "pystray",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "client.app.collector.main",  # main.py를 import하므로 포함
    "client.core.pc_identifier",  # pc_identifier 포함
]

for imp in hidden_imports:
    build_options.extend(["--hidden-import", imp])

# 빌드 실행
print("=" * 60)
print("샷 수집 GUI 프로그램 빌드 시작")
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
print("   2. config 폴더와 regions 폴더도 함께 복사 (필요시)")
print("   3. 실행하면 GUI 창이 나타남")
print("   4. 브랜드 선택 → 좌표 파일 선택 → 시작 버튼 클릭")
print("   5. 시작 후 2초 뒤 트레이로 이동")
print("=" * 60)
