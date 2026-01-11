# ===== build_exe.py (Windows 실행 파일 빌드 스크립트) =====
"""
main.py를 Windows 실행 파일(.exe)로 빌드하는 스크립트

사용 방법:
    python build_exe.py

결과:
    dist/main.exe 파일이 생성됩니다.
"""

import subprocess
import sys
import os

def build_exe():
    """PyInstaller를 사용하여 main.py를 실행 파일로 빌드"""
    
    print("🔨 Windows 실행 파일 빌드 시작...")
    print("=" * 60)
    
    # PyInstaller 설치 확인
    try:
        import PyInstaller
        print("✅ PyInstaller 설치 확인됨")
    except ImportError:
        print("❌ PyInstaller가 설치되지 않았습니다.")
        print("   설치 중: pip install pyinstaller")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller 설치 완료")
    
    # PyInstaller 명령어 구성
    cmd = [
        "pyinstaller",
        "--onefile",                    # 단일 실행 파일로 생성
        "--windowed",                   # 콘솔 창 숨김 (필요시 --console로 변경)
        "--name=GolfShotTracker",       # 실행 파일 이름
        "--icon=NONE",                  # 아이콘 (필요시 추가)
        "--add-data=config;config",     # config 폴더 포함
        "--add-data=regions;regions",    # regions 폴더 포함
        "--hidden-import=pyttsx3.drivers",  # TTS 드라이버 포함
        "--hidden-import=pyttsx3.drivers.sapi5",  # Windows TTS 드라이버
        "--hidden-import=openai",       # OpenAI 라이브러리 (차후 사용)
        "--hidden-import=cv2",          # OpenCV
        "--hidden-import=pytesseract",  # Tesseract OCR
        "--hidden-import=numpy",        # NumPy
        "--hidden-import=PIL",          # Pillow
        "--hidden-import=requests",    # Requests
        "--hidden-import=pyautogui",   # PyAutoGUI
        "--clean",                      # 빌드 전 정리
        "main.py"                       # 메인 스크립트
    ]
    
    print("\n📦 빌드 명령어:")
    print(" ".join(cmd))
    print("\n" + "=" * 60)
    print("⏳ 빌드 중... (시간이 걸릴 수 있습니다)")
    print("=" * 60 + "\n")
    
    try:
        # PyInstaller 실행
        subprocess.check_call(cmd)
        
        print("\n" + "=" * 60)
        print("✅ 빌드 완료!")
        print("=" * 60)
        print(f"\n📁 실행 파일 위치: dist/GolfShotTracker.exe")
        print(f"📁 빌드 파일 위치: build/ 폴더")
        print("\n💡 사용 방법:")
        print("   1. dist/GolfShotTracker.exe 파일을 골프 컴퓨터로 복사")
        print("   2. config/ 폴더와 regions/ 폴더도 함께 복사")
        print("   3. GolfShotTracker.exe 실행")
        print("\n⚠️  주의사항:")
        print("   - Tesseract OCR이 골프 컴퓨터에 설치되어 있어야 합니다")
        print("   - config/ 폴더와 regions/ 폴더가 exe 파일과 같은 위치에 있어야 합니다")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 빌드 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()
