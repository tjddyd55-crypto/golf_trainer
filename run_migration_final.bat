@echo off
chcp 65001 >nul
echo ============================================================
echo 데이터베이스 마이그레이션 실행
echo ============================================================
echo.
echo Railway PostgreSQL의 DATABASE_PUBLIC_URL을 입력하세요.
echo.
echo Railway 대시보드 ^> PostgreSQL 서비스 ^> Variables 탭
echo DATABASE_PUBLIC_URL 값을 복사하세요.
echo.
echo 예시: postgresql://postgres:password@crossover.proxy.rlwy.net:26154/railway
echo.
echo ============================================================
echo.

set /p DATABASE_URL="DATABASE_PUBLIC_URL을 입력하세요: "

if "%DATABASE_URL%"=="" (
    echo.
    echo [오류] DATABASE_URL이 입력되지 않았습니다.
    pause
    exit /b 1
)

echo.
echo 마이그레이션 실행 중...
echo.

REM Python 스크립트에 URL을 직접 전달 (환경 변수 문제 회피)
python -c "import os; os.environ['DATABASE_URL'] = r'%DATABASE_URL%'; exec(open('run_migration_direct.py').read())"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 마이그레이션 실행 중 오류가 발생했습니다.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 마이그레이션 완료!
echo ============================================================
pause
