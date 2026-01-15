@echo off
chcp 65001 >nul
echo ========================================
echo coordinates 테이블 생성
echo ========================================
echo.

python create_coordinates_table.py

if %ERRORLEVEL% EQU 0 (
    echo.
) else (
    echo.
    echo DATABASE_URL 환경 변수를 확인하세요.
)

echo.
pause
