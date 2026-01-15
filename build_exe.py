# ===== build_exe.py (Windows 실행 파일 빌드 스크립트) =====
"""
GolfShotTracker.spec 파일을 사용하여 Windows 실행 파일(.exe)로 빌드하는 스크립트

사용 방법:
    python build_exe.py

결과:
    dist/GolfShotTracker.exe 파일이 생성됩니다.

주의:
    - GolfShotTracker.spec 파일이 존재해야 합니다
    - 빌드 옵션(--onefile, --windowed, --add-data, --hidden-import)은
      spec 파일에 정의되어 있습니다
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def build_exe():
    """PyInstaller를 사용하여 spec 파일로 빌드"""
    
    print("Windows 실행 파일 빌드 시작...")
    print("=" * 60)
    
    # spec 파일 경로
    spec_file = Path("GolfShotTracker.spec")
    
    # spec 파일 존재 확인
    if not spec_file.exists():
        print(f"[ERROR] GolfShotTracker.spec 파일을 찾을 수 없습니다.")
        print(f"   현재 디렉토리: {os.getcwd()}")
        print(f"   예상 경로: {spec_file.absolute()}")
        sys.exit(1)
    
    print(f"[OK] spec 파일 확인: {spec_file.absolute()}")
    
    # PyInstaller 설치 확인
    try:
        import PyInstaller
        print("[OK] PyInstaller 설치 확인됨")
    except ImportError:
        print("[ERROR] PyInstaller가 설치되지 않았습니다.")
        print("   설치 중: pip install pyinstaller")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller 설치 완료")
    
    # build/와 dist/ 폴더 삭제
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        print(f"[INFO] build/ 폴더 삭제 중...")
        try:
            shutil.rmtree(build_dir)
            print(f"[OK] build/ 폴더 삭제 완료")
        except Exception as e:
            print(f"[WARNING] build/ 폴더 삭제 실패 (계속 진행): {e}")
    
    if dist_dir.exists():
        print(f"[INFO] dist/ 폴더 삭제 중...")
        try:
            shutil.rmtree(dist_dir)
            print(f"[OK] dist/ 폴더 삭제 완료")
        except Exception as e:
            print(f"[WARNING] dist/ 폴더 삭제 실패 (계속 진행): {e}")
            print(f"[INFO] dist/ 폴더가 사용 중일 수 있습니다. exe 파일을 닫고 다시 시도하세요.")
    
    # PyInstaller 명령어 구성 (spec 파일만 사용)
    cmd = [
        "pyinstaller",
        str(spec_file),
        "--clean"
    ]
    
    print("\n[INFO] 빌드 명령어:")
    print(" ".join(cmd))
    print("\n[INFO] 빌드 옵션은 GolfShotTracker.spec 파일에 정의되어 있습니다")
    print("=" * 60)
    print("[INFO] 빌드 중... (시간이 걸릴 수 있습니다)")
    print("=" * 60 + "\n")
    
    try:
        # PyInstaller 실행
        subprocess.check_call(cmd)
        
        print("\n" + "=" * 60)
        print("[OK] 빌드 완료!")
        print("=" * 60)
        print(f"\n[INFO] 실행 파일 위치: dist/GolfShotTracker.exe")
        print(f"[INFO] 빌드 파일 위치: build/ 폴더")
        print("\n[INFO] 사용 방법:")
        print("   1. dist/GolfShotTracker.exe 파일을 골프 컴퓨터로 복사")
        print("   2. GolfShotTracker.exe 실행 (config/와 regions/ 폴더는 자동 생성됨)")
        print("\n[INFO] onefile 배포 특징:")
        print("   - 단일 exe 파일로 배포 가능 (의존성 폴더 불필요)")
        print("   - 첫 실행 시 exe와 같은 위치에 config/와 regions/ 폴더 자동 생성")
        print("   - bundled 리소스(config/criteria.json, regions/test.json)가 자동 복사됨")
        print("\n[WARNING] 주의사항:")
        print("   - Tesseract OCR이 골프 컴퓨터에 설치되어 있어야 합니다")
        print("   - config.json 파일은 수동으로 생성하거나 서버에서 로드해야 합니다")
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] 빌드 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()
