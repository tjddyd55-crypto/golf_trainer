@echo off
chcp 65001 >nul
echo ============================================================
echo 데이터베이스 마이그레이션 실행 (자동)
echo ============================================================
echo.

REM Railway PostgreSQL 정보 입력
set /p DB_HOST="PostgreSQL 호스트 (예: postgres-production-09f4.up.railway.app): "
set /p DB_PORT="포트 (기본값: 5432): "
set /p DB_USER="사용자명 (기본값: postgres): "
set /p DB_PASSWORD="비밀번호: "
set /p DB_NAME="데이터베이스명 (기본값: railway): "

if "%DB_HOST%"=="" (
    echo [오류] 호스트가 입력되지 않았습니다.
    pause
    exit /b 1
)

if "%DB_PORT%"=="" set DB_PORT=5432
if "%DB_USER%"=="" set DB_USER=postgres
if "%DB_NAME%"=="" set DB_NAME=railway

if "%DB_PASSWORD%"=="" (
    echo [오류] 비밀번호가 입력되지 않았습니다.
    pause
    exit /b 1
)

REM DATABASE_URL 구성
set DATABASE_URL=postgresql://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%

echo.
echo 구성된 DATABASE_URL: postgresql://%DB_USER%:***@%DB_HOST%:%DB_PORT%/%DB_NAME%
echo.
echo 마이그레이션 실행 중...
echo.

python -c "import os; os.environ['DATABASE_URL'] = r'%DATABASE_URL%'; exec(open('run_migration_with_url.py').read().replace('DATABASE_URL = input', '# DATABASE_URL = input').replace('sys.exit(1)', 'pass'))"

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
