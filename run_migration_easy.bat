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

REM 임시 Python 스크립트 생성하여 실행 (특수 문자 처리)
echo import os > temp_migration.py
echo import sys >> temp_migration.py
echo. >> temp_migration.py
echo # DATABASE_URL 설정 >> temp_migration.py
echo DATABASE_URL = r'%DATABASE_URL%' >> temp_migration.py
echo os.environ['DATABASE_URL'] = DATABASE_URL >> temp_migration.py
echo. >> temp_migration.py
echo # 마이그레이션 실행 >> temp_migration.py
echo exec(open('run_migration_direct.py', encoding='utf-8').read()) >> temp_migration.py

python temp_migration.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 마이그레이션 실행 중 오류가 발생했습니다.
    del temp_migration.py
    pause
    exit /b 1
)

del temp_migration.py

echo.
echo ============================================================
echo 마이그레이션 완료!
echo ============================================================
pause
