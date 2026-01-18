@echo off
REM ===== Baseline 로그 저장 스크립트 =====
REM 리팩터링 전 기준 로그를 저장합니다.

setlocal enabledelayedexpansion

echo ========================================
echo Baseline 로그 저장 시작
echo ========================================
echo.

REM baseline 폴더 생성
if not exist "baseline_logs" mkdir baseline_logs

REM 타임스탬프 생성
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%"
set "Min=%dt:~10,2%"
set "SS=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%SS%"

echo [%timestamp%] Baseline 로그 저장
echo.

REM 1. 샷 수집 프로그램 로그
echo [1/3] 샷 수집 프로그램 로그 확인...
if exist "runtime.log" (
    copy "runtime.log" "baseline_logs\shot_collector_runtime_%timestamp%.log" >nul
    echo   - runtime.log 저장 완료
) else (
    echo   - runtime.log 없음 (정상: 아직 실행 안 함)
)

if exist "error.log" (
    copy "error.log" "baseline_logs\shot_collector_error_%timestamp%.log" >nul
    echo   - error.log 저장 완료
) else (
    echo   - error.log 없음 (정상: 에러 없음)
)

if exist "early_debug.log" (
    copy "early_debug.log" "baseline_logs\shot_collector_early_debug_%timestamp%.log" >nul
    echo   - early_debug.log 저장 완료
) else (
    echo   - early_debug.log 없음
)

if exist "logs" (
    xcopy /E /I /Y "logs" "baseline_logs\shot_collector_logs_%timestamp%" >nul
    echo   - logs 폴더 저장 완료
) else (
    echo   - logs 폴더 없음
)

echo.

REM 2. PC 등록 프로그램 로그
echo [2/3] PC 등록 프로그램 로그 확인...
if exist "pc_registration.log" (
    copy "pc_registration.log" "baseline_logs\pc_registration_%timestamp%.log" >nul
    echo   - pc_registration.log 저장 완료
) else (
    echo   - pc_registration.log 없음 (정상: 로그 파일 없을 수 있음)
)

echo.

REM 3. 좌표 설정 프로그램 로그
echo [3/3] 좌표 설정 프로그램 로그 확인...
if exist "calibration.log" (
    copy "calibration.log" "baseline_logs\calibration_%timestamp%.log" >nul
    echo   - calibration.log 저장 완료
) else (
    echo   - calibration.log 없음 (정상: 로그 파일 없을 수 있음)
)

echo.
echo ========================================
echo Baseline 로그 저장 완료
echo ========================================
echo 저장 위치: baseline_logs\
echo 타임스탬프: %timestamp%
echo.
pause
