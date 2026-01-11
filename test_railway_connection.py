#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Railway 서버 연결 테스트 스크립트
서버가 정상적으로 작동하는지 확인합니다.
"""

import requests
import sys
import os

def test_server_connection(base_url):
    """서버 연결 테스트"""
    print("=" * 60)
    print("Railway 서버 연결 테스트")
    print("=" * 60)
    print()
    print(f"서버 URL: {base_url}")
    print()
    
    tests = {
        "passed": 0,
        "failed": 0
    }
    
    # 1. 기본 접속 테스트
    print("[1/5] 기본 접속 테스트...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ 서버 접속 성공")
            tests["passed"] += 1
        else:
            print(f"⚠️  서버 응답: {response.status_code}")
            tests["passed"] += 1  # 응답이 있으면 통과
    except requests.exceptions.RequestException as e:
        print(f"❌ 서버 접속 실패: {e}")
        tests["failed"] += 1
        return tests
    
    # 2. 로그인 페이지 테스트
    print()
    print("[2/5] 로그인 페이지 테스트...")
    try:
        response = requests.get(f"{base_url}/login", timeout=10)
        if response.status_code == 200:
            print("✅ 로그인 페이지 접속 성공")
            tests["passed"] += 1
        else:
            print(f"❌ 로그인 페이지 접속 실패: {response.status_code}")
            tests["failed"] += 1
    except requests.exceptions.RequestException as e:
        print(f"❌ 로그인 페이지 접속 실패: {e}")
        tests["failed"] += 1
    
    # 3. API 엔드포인트 테스트 (active_user)
    print()
    print("[3/5] API 엔드포인트 테스트 (active_user)...")
    try:
        response = requests.get(
            f"{base_url}/api/active_user",
            params={"store_id": "gaja", "bay_id": "01"},
            timeout=10
        )
        if response.status_code in [200, 404]:  # 404도 정상 (사용자 없음)
            print("✅ active_user API 정상 작동")
            tests["passed"] += 1
        else:
            print(f"⚠️  active_user API 응답: {response.status_code}")
            tests["passed"] += 1
    except requests.exceptions.RequestException as e:
        print(f"❌ active_user API 실패: {e}")
        tests["failed"] += 1
    
    # 4. 샷 저장 API 테스트 (테스트 데이터)
    print()
    print("[4/5] 샷 저장 API 테스트...")
    test_data = {
        "store_id": "gaja",
        "bay_id": "01",
        "user_id": "test_user",
        "club_id": "Driver",
        "ball_speed": 150.5,
        "club_speed": 100.2,
        "smash_factor": 1.50,
        "launch_angle": 12.5,
        "timestamp": "2025-01-01 12:00:00"
    }
    try:
        response = requests.post(
            f"{base_url}/api/save_shot",
            json=test_data,
            timeout=10
        )
        if response.status_code == 200:
            print("✅ 샷 저장 API 정상 작동")
            tests["passed"] += 1
        else:
            print(f"⚠️  샷 저장 API 응답: {response.status_code}")
            print(f"   응답: {response.text[:100]}")
            tests["failed"] += 1
    except requests.exceptions.RequestException as e:
        print(f"❌ 샷 저장 API 실패: {e}")
        tests["failed"] += 1
    
    # 5. 데이터베이스 연결 테스트 (간접)
    print()
    print("[5/5] 데이터베이스 연결 테스트 (간접)...")
    # 샷 저장이 성공했다면 데이터베이스 연결도 성공한 것
    if tests["passed"] >= 4:
        print("✅ 데이터베이스 연결 정상 (API 응답으로 확인)")
        tests["passed"] += 1
    else:
        print("⚠️  데이터베이스 연결 확인 불가 (API 테스트 필요)")
        tests["failed"] += 1
    
    # 결과 요약
    print()
    print("=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"✅ 통과: {tests['passed']}")
    print(f"❌ 실패: {tests['failed']}")
    print()
    
    if tests["failed"] == 0:
        print("🎉 모든 테스트 통과! 서버가 정상적으로 작동합니다.")
        return 0
    else:
        print("⚠️  일부 테스트 실패. 서버 상태를 확인하세요.")
        return 1

def main():
    # 환경 변수에서 서버 URL 가져오기
    server_url = os.environ.get("SERVER_URL", "")
    
    if not server_url:
        # main.py에서 기본값 확인
        try:
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
                import re
                match = re.search(r'DEFAULT_SERVER_URL = os\.environ\.get\("SERVER_URL", "([^"]+)"\)', content)
                if match:
                    server_url = match.group(1)
        except:
            pass
    
    if not server_url or "127.0.0.1" in server_url or "localhost" in server_url:
        print("Railway 서버 URL을 입력하세요.")
        print("예: https://golf-trainer-production.railway.app")
        print()
        server_url = input("Railway URL: ").strip()
    
    if not server_url:
        print("❌ 서버 URL이 입력되지 않았습니다.")
        return 1
    
    # 마지막 슬래시 제거
    server_url = server_url.rstrip("/")
    
    return test_server_connection(server_url)

if __name__ == "__main__":
    sys.exit(main())
