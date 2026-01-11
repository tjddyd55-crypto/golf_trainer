@echo off
REM ========================================
REM Golf Trainer 클라이언트 시작 스크립트
REM ========================================
REM 사용 방법:
REM 1. Railway 서버 URL을 아래에 입력
REM 2. 이 파일을 더블클릭하여 실행
REM ========================================

REM ⚠️ 여기에 Railway 서버 URL을 입력하세요
set SERVER_URL=https://your-railway-app.railway.app

REM 서버 URL 확인
if "%SERVER_URL%"=="" (
    echo ❌ 오류: SERVER_URL이 설정되지 않았습니다.
    echo 이 파일을 텍스트 에디터로 열어 SERVER_URL을 설정해주세요.
    pause
    exit /b 1
)

echo ========================================
echo Golf Trainer 클라이언트 시작
echo ========================================
echo 서버 URL: %SERVER_URL%
echo ========================================
echo.

REM Python 실행
python main.py

REM 실행 후 창 유지
if errorlevel 1 (
    echo.
    echo ❌ 오류가 발생했습니다.
    pause
)
