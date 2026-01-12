#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
등록 코드 생성 프로그램 (슈퍼 관리자 API 사용)
"""
import requests
import sys
import os

def main():
    print("=" * 60)
    print("등록 코드 생성 프로그램")
    print("=" * 60)
    print()
    
    # 슈퍼 관리자 API URL (환경 변수 또는 기본값)
    api_url = os.environ.get("SUPER_ADMIN_URL", "https://golf-super-admin-production.up.railway.app")
    
    # 슈퍼 관리자 로그인 정보
    print("슈퍼 관리자 로그인 정보를 입력하세요:")
    username = input("사용자명: ").strip()
    password = input("비밀번호: ").strip()
    
    if not username or not password:
        print("[ERROR] 사용자명과 비밀번호를 입력해야 합니다.")
        return 1
    
    print()
    print("로그인 중...")
    
    # 로그인 세션 생성
    session = requests.Session()
    login_url = f"{api_url}/login"
    
    try:
        # 로그인
        login_response = session.post(
            login_url,
            data={"username": username, "password": password},
            timeout=10,
            allow_redirects=False  # 리다이렉트를 수동으로 처리
        )
        
        # Flask 로그인 성공 시 302 리다이렉트 반환
        # 실패 시 200 (에러 페이지) 또는 다른 상태 코드
        if login_response.status_code == 302:
            # 리다이렉트 위치 확인
            location = login_response.headers.get('Location', '')
            if 'super_admin_dashboard' in location or 'dashboard' in location:
                print("[OK] 로그인 성공")
                print()
            else:
                print("[ERROR] 로그인 실패. 사용자명 또는 비밀번호를 확인하세요.")
                return 1
        elif login_response.status_code == 200:
            # 200 응답이면 에러 페이지일 가능성
            if "인증 실패" in login_response.text or "error" in login_response.text.lower():
                print("[ERROR] 로그인 실패. 사용자명 또는 비밀번호를 확인하세요.")
                return 1
            else:
                print("[OK] 로그인 성공")
                print()
        else:
            print(f"[ERROR] 로그인 실패. 상태 코드: {login_response.status_code}")
            return 1
        
        # 등록 코드 생성 요청
        print("등록 코드 생성 중...")
        create_url = f"{api_url}/api/create_registration_code"
        
        create_response = session.post(
            create_url,
            json={"notes": "PC 등록 프로그램을 통해 생성된 코드"},
            timeout=10
        )
        
        if create_response.status_code == 200:
            data = create_response.json()
            if data.get("success"):
                registration_code = data.get("registration_code") or data.get("registration_key")
                
                print()
                print("=" * 60)
                print("[OK] 등록 코드 생성 완료!")
                print("=" * 60)
                print()
                print(f"등록 코드: {registration_code}")
                print(f"상태: {data.get('status', 'ACTIVE')}")
                print()
                print("=" * 60)
                print("이 코드를 PC 등록 프로그램에서 사용하세요.")
                print("=" * 60)
                print()
                return 0
            else:
                print(f"[ERROR] 등록 코드 생성 실패: {data.get('message', '알 수 없는 오류')}")
                return 1
        else:
            print(f"[ERROR] 서버 오류: {create_response.status_code}")
            try:
                error_data = create_response.json()
                print(f"   오류: {error_data.get('message', create_response.text)}")
            except:
                print(f"   응답: {create_response.text}")
            return 1
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] 서버 연결 실패: {api_url}")
        print("   서버 URL이 올바른지 확인해주세요.")
        return 1
    except requests.exceptions.Timeout:
        print("[ERROR] 서버 응답 시간 초과")
        return 1
    except Exception as e:
        print(f"[ERROR] 등록 코드 생성 실패: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
