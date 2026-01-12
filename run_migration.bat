@echo off
chcp 65001 >nul
echo ============================================================
echo 데이터베이스 마이그레이션 실행
echo ============================================================
echo.
echo Railway PostgreSQL의 전체 DATABASE_URL이 필요합니다.
echo.
echo Railway 대시보드 ^> PostgreSQL 서비스 ^> Connect 탭
echo Public Network 섹션의 전체 URL을 복사하세요.
echo.
echo 예시: postgresql://postgres:password@postgres-production-09f4.up.railway.app:5432/railway
echo.
echo ============================================================
echo.

set /p DATABASE_URL="DATABASE_URL을 입력하세요: "

if "%DATABASE_URL%"=="" (
    echo.
    echo [오류] DATABASE_URL이 입력되지 않았습니다.
    pause
    exit /b 1
)

echo.
echo 마이그레이션 실행 중...
echo.

set DATABASE_URL=%DATABASE_URL%
python run_migration_direct.py

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
