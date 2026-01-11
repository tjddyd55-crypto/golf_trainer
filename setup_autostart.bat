@echo off
REM ===== setup_autostart.bat (Windows 시작 시 자동 실행 설정) =====
REM 샷 수집 프로그램을 Windows 시작 프로그램에 등록

echo ============================================================
echo 샷 수집 프로그램 자동 실행 설정
echo ============================================================
echo.

REM 현재 스크립트 위치 확인
set SCRIPT_DIR=%~dp0
set EXE_PATH=%SCRIPT_DIR%shot_collector.exe

REM 실행 파일 존재 확인
if not exist "%EXE_PATH%" (
    echo [오류] shot_collector.exe 파일을 찾을 수 없습니다.
    echo 파일 위치: %EXE_PATH%
    echo.
    pause
    exit /b 1
)

echo 실행 파일 위치: %EXE_PATH%
echo.

REM 시작 프로그램 폴더 경로
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_NAME=GolfShotCollector.lnk

echo 시작 프로그램 폴더: %STARTUP_FOLDER%
echo.

REM PowerShell을 사용하여 바로가기 생성
echo 바로가기 생성 중...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\%SHORTCUT_NAME%'); $Shortcut.TargetPath = '%EXE_PATH%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Save()"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo ✅ 자동 실행 설정 완료!
    echo ============================================================
    echo.
    echo 다음 부팅 시 자동으로 실행됩니다.
    echo.
    echo 자동 실행을 해제하려면:
    echo   시작 프로그램 폴더에서 GolfShotCollector.lnk 삭제
    echo.
) else (
    echo.
    echo ============================================================
    echo ❌ 자동 실행 설정 실패
    echo ============================================================
    echo.
    echo 관리자 권한으로 실행해보세요.
    echo.
)

pause
