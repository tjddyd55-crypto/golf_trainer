@echo off
REM PC 등록 프로그램 테스트 스크립트
REM Railway API 서비스 URL을 환경 변수로 설정 (필요시)

REM Railway API 서비스 URL 설정 (실제 URL로 변경 필요)
REM set SERVER_URL=https://golf-api-production.up.railway.app

echo ============================================================
echo PC 등록 프로그램 테스트
echo ============================================================
echo.
echo Railway API 서비스 URL을 확인하세요:
echo   1. Railway 대시보드 열기
echo   2. golf-api 서비스 선택
echo   3. Settings - Domains 또는 Deployments 탭에서 URL 확인
echo.
echo 환경 변수 설정 (필요시):
echo   set SERVER_URL=실제_서버_URL
echo.
echo ============================================================
echo.

REM PC 등록 프로그램 실행
cd /d "%~dp0"
dist\register_pc.exe

pause
