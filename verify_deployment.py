#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
배포 전 검증 스크립트
Railway 배포 전에 모든 설정이 올바른지 확인합니다.
"""

import os
import json
import sys

# 색상 출력
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    try:
        print(f"{Colors.GREEN}[OK] {msg}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[OK] {msg}")

def print_error(msg):
    try:
        print(f"{Colors.RED}[FAIL] {msg}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[FAIL] {msg}")

def print_warning(msg):
    try:
        print(f"{Colors.YELLOW}[WARN] {msg}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[WARN] {msg}")

def print_info(msg):
    try:
        print(f"{Colors.BLUE}[INFO] {msg}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[INFO] {msg}")

def print_header(msg):
    try:
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    except UnicodeEncodeError:
        # Windows 콘솔 호환
        print(f"\n{'='*60}")
        print(f"{msg}")
        print(f"{'='*60}\n")

# 검증 결과
checks = {
    "passed": 0,
    "failed": 0,
    "warnings": 0
}

def check_file_exists(filepath, description):
    """파일 존재 확인"""
    if os.path.exists(filepath):
        print_success(f"{description}: {filepath}")
        checks["passed"] += 1
        return True
    else:
        print_error(f"{description} 없음: {filepath}")
        checks["failed"] += 1
        return False

def check_file_content(filepath, keyword, description):
    """파일 내용 확인"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if keyword in content:
                print_success(f"{description}: {keyword} 확인됨")
                checks["passed"] += 1
                return True
            else:
                print_error(f"{description}: {keyword} 없음")
                checks["failed"] += 1
                return False
    except Exception as e:
        print_error(f"{description} 파일 읽기 오류: {e}")
        checks["failed"] += 1
        return False

def check_json_valid(filepath, description):
    """JSON 파일 유효성 확인"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        print_success(f"{description}: JSON 형식 올바름")
        checks["passed"] += 1
        return True
    except json.JSONDecodeError as e:
        print_error(f"{description}: JSON 형식 오류 - {e}")
        checks["failed"] += 1
        return False
    except Exception as e:
        print_error(f"{description} 파일 읽기 오류: {e}")
        checks["failed"] += 1
        return False

def check_python_syntax(filepath, description):
    """Python 문법 확인"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, filepath, 'exec')
        print_success(f"{description}: Python 문법 올바름")
        checks["passed"] += 1
        return True
    except SyntaxError as e:
        print_error(f"{description}: Python 문법 오류 - {e}")
        checks["failed"] += 1
        return False
    except Exception as e:
        print_error(f"{description} 파일 읽기 오류: {e}")
        checks["failed"] += 1
        return False

def main():
    print_header("[1/11] Golf Trainer 배포 검증 시작")
    
    # 1. 필수 파일 확인
    print_header("[1/11] 필수 파일 확인")
    check_file_exists("Procfile", "Procfile")
    check_file_exists("requirements.txt", "requirements.txt")
    check_file_exists("railway.json", "railway.json")
    check_file_exists("app.py", "Flask 앱 (app.py)")
    check_file_exists("database.py", "데이터베이스 (database.py)")
    check_file_exists("main.py", "클라이언트 (main.py)")
    check_file_exists(".gitignore", ".gitignore")
    
    # 2. Procfile 검증
    print_header("[2/11] Procfile 검증")
    if check_file_content("Procfile", "gunicorn", "gunicorn 사용"):
        check_file_content("Procfile", "$PORT", "환경 변수 PORT 사용")
        check_file_content("Procfile", "app:app", "Flask 앱 연결")
    
    # 3. requirements.txt 검증
    print_header("[3/11] requirements.txt 검증")
    required_packages = [
        "flask",
        "gunicorn",
        "psycopg2-binary",
        "opencv-python",
        "pytesseract",
        "requests",
        "pyttsx3",
        "pyautogui"
    ]
    try:
        with open("requirements.txt", 'r', encoding='utf-8') as f:
            content = f.read().lower()
            for package in required_packages:
                if package.lower() in content:
                    print_success(f"필수 패키지: {package}")
                    checks["passed"] += 1
                else:
                    print_error(f"필수 패키지 없음: {package}")
                    checks["failed"] += 1
    except Exception as e:
        print_error(f"requirements.txt 읽기 오류: {e}")
        checks["failed"] += 1
    
    # 4. railway.json 검증
    print_header("[4/11] railway.json 검증")
    if check_json_valid("railway.json", "railway.json"):
        try:
            with open("railway.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "deploy" in config and "startCommand" in config["deploy"]:
                    print_success("startCommand 설정 확인")
                    checks["passed"] += 1
                else:
                    print_error("startCommand 설정 없음")
                    checks["failed"] += 1
        except Exception:
            pass
    
    # 5. 환경 변수 사용 확인
    print_header("[5/11] 환경 변수 사용 확인")
    check_file_content("app.py", "os.environ.get(\"PORT\"", "app.py - PORT 환경 변수")
    check_file_content("app.py", "os.environ.get(\"FLASK_SECRET_KEY\"", "app.py - FLASK_SECRET_KEY 환경 변수")
    check_file_content("database.py", "os.environ.get(\"DATABASE_URL\"", "database.py - DATABASE_URL 환경 변수")
    check_file_content("main.py", "os.environ.get(\"SERVER_URL\"", "main.py - SERVER_URL 환경 변수")
    
    # 6. PostgreSQL 설정 확인
    print_header("[6/11] PostgreSQL 설정 확인")
    check_file_content("database.py", "psycopg2", "psycopg2 사용")
    check_file_content("database.py", "RealDictCursor", "RealDictCursor 사용")
    check_file_content("requirements.txt", "psycopg2-binary", "psycopg2-binary 패키지")
    
    # 7. Python 문법 확인
    print_header("[7/11] Python 문법 확인")
    check_python_syntax("app.py", "app.py")
    check_python_syntax("database.py", "database.py")
    check_python_syntax("main.py", "main.py")
    
    # 8. 설정 파일 확인
    print_header("[8/11] 설정 파일 확인")
    check_file_exists("config/criteria.json", "criteria.json")
    check_file_exists("config/feedback_messages.json", "feedback_messages.json")
    if os.path.exists("config/criteria.json"):
        check_json_valid("config/criteria.json", "criteria.json")
    if os.path.exists("config/feedback_messages.json"):
        check_json_valid("config/feedback_messages.json", "feedback_messages.json")
    
    # 9. 템플릿 파일 확인
    print_header("[9/11] 템플릿 파일 확인")
    templates = [
        "templates/index.html",
        "templates/user_login.html",
        "templates/user_main.html",
        "templates/admin_login.html",
        "templates/admin.html",
        "templates/shots_all.html"
    ]
    for template in templates:
        check_file_exists(template, f"템플릿: {os.path.basename(template)}")
    
    # 10. 클라이언트 설정 파일 확인
    print_header("[10/11] 클라이언트 설정 파일 확인")
    check_file_exists("start_client.bat", "start_client.bat")
    if os.path.exists("regions/test.json"):
        check_json_valid("regions/test.json", "regions/test.json")
        print_success("OCR 영역 설정 파일 확인")
        checks["passed"] += 1
    else:
        print_warning("regions/test.json 없음 (선택사항)")
        checks["warnings"] += 1
    
    # 11. Git 상태 확인
    print_header("[11/11] Git 상태 확인")
    if os.path.exists(".git"):
        print_success("Git 저장소 초기화됨")
        checks["passed"] += 1
        
        # .gitignore 확인
        if os.path.exists(".gitignore"):
            with open(".gitignore", 'r', encoding='utf-8') as f:
                ignore_content = f.read()
                if "*.db" in ignore_content or "golf_data.db" in ignore_content:
                    print_success(".gitignore에 데이터베이스 파일 제외 설정")
                    checks["passed"] += 1
                else:
                    print_warning(".gitignore에 데이터베이스 파일 제외 권장")
                    checks["warnings"] += 1
    else:
        print_warning("Git 저장소가 초기화되지 않음")
        checks["warnings"] += 1
    
    # 결과 요약
    print_header("[결과] 검증 결과 요약")
    try:
        print(f"{Colors.GREEN}통과: {checks['passed']}{Colors.RESET}")
        print(f"{Colors.RED}실패: {checks['failed']}{Colors.RESET}")
        print(f"{Colors.YELLOW}경고: {checks['warnings']}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"통과: {checks['passed']}")
        print(f"실패: {checks['failed']}")
        print(f"경고: {checks['warnings']}")
    print()
    
    if checks["failed"] == 0:
        print_success("모든 검증 통과! Railway 배포 준비 완료!")
        print()
        print_info("다음 단계:")
        print("1. Git 커밋 및 GitHub 푸시")
        print("2. Railway에서 프로젝트 생성 및 배포")
        print("3. PostgreSQL 서비스 추가")
        print("4. 클라이언트 서버 URL 설정")
        return 0
    else:
        print_error("일부 검증 실패. 위의 오류를 확인하고 수정하세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
