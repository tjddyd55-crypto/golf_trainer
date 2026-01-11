#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Railway 서버로 전환 스크립트
로컬 환경에서 Railway 서버로 전환하는 도우미 스크립트
"""

import os
import sys
import re

def update_main_py(railway_url):
    """main.py의 서버 URL을 Railway URL로 업데이트"""
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # DEFAULT_SERVER_URL 업데이트
        pattern = r'DEFAULT_SERVER_URL = os\.environ\.get\("SERVER_URL", ".*?"\)'
        replacement = f'DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "{railway_url}")'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open("main.py", "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ main.py 업데이트 완료: {railway_url}")
            return True
        else:
            print("⚠️  main.py에 변경사항이 없습니다.")
            return False
    except Exception as e:
        print(f"❌ main.py 업데이트 실패: {e}")
        return False

def update_bat_file(railway_url):
    """start_client.bat의 서버 URL 업데이트"""
    try:
        with open("start_client.bat", "r", encoding="utf-8") as f:
            content = f.read()
        
        # SERVER_URL 업데이트
        pattern = r'set SERVER_URL=.*'
        replacement = f'set SERVER_URL={railway_url}'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open("start_client.bat", "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ start_client.bat 업데이트 완료: {railway_url}")
            return True
        else:
            print("⚠️  start_client.bat에 변경사항이 없습니다.")
            return False
    except Exception as e:
        print(f"❌ start_client.bat 업데이트 실패: {e}")
        return False

def validate_url(url):
    """URL 형식 검증"""
    if not url.startswith("http://") and not url.startswith("https://"):
        return False
    if "railway.app" not in url and "localhost" not in url and "127.0.0.1" not in url:
        print("⚠️  경고: Railway URL이 아닌 것 같습니다.")
    return True

def main():
    print("=" * 60)
    print("Railway 서버로 전환")
    print("=" * 60)
    print()
    
    # Railway URL 입력
    print("Railway 서버 URL을 입력하세요.")
    print("예: https://golf-trainer-production.railway.app")
    print()
    
    railway_url = input("Railway URL: ").strip()
    
    if not railway_url:
        print("❌ URL이 입력되지 않았습니다.")
        return 1
    
    # URL 검증
    if not validate_url(railway_url):
        print("❌ 올바른 URL 형식이 아닙니다. (http:// 또는 https://로 시작해야 함)")
        return 1
    
    # 마지막 슬래시 제거
    railway_url = railway_url.rstrip("/")
    
    print()
    print(f"Railway URL: {railway_url}")
    print()
    
    # 확인
    confirm = input("이 URL로 업데이트하시겠습니까? (y/n): ").strip().lower()
    if confirm != "y":
        print("취소되었습니다.")
        return 0
    
    print()
    print("업데이트 중...")
    print()
    
    # 파일 업데이트
    main_updated = update_main_py(railway_url)
    bat_updated = update_bat_file(railway_url)
    
    print()
    print("=" * 60)
    if main_updated or bat_updated:
        print("✅ 업데이트 완료!")
        print()
        print("다음 단계:")
        print("1. 기능 테스트를 진행하세요")
        print("2. start_client.bat를 실행하여 클라이언트를 시작하세요")
        print("3. 또는 환경 변수로 설정:")
        print(f'   set SERVER_URL={railway_url}')
        print("   python main.py")
    else:
        print("⚠️  변경사항이 없습니다.")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
