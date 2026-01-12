#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
테스트용 등록 코드 생성 스크립트
"""
import sys
import os

# 공유 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import database

def main():
    print("=" * 60)
    print("테스트용 등록 코드 생성")
    print("=" * 60)
    print()
    
    # 데이터베이스 초기화
    database.init_db()
    
    # 등록 코드 생성
    print("등록 코드 생성 중...")
    code_data = database.create_registration_code(
        issued_by="test_admin",
        notes="테스트용 등록 코드"
    )
    
    if code_data:
        registration_code = code_data.get("code")
        status = code_data.get("status")
        
        print()
        print("=" * 60)
        print("[OK] 등록 코드 생성 완료!")
        print("=" * 60)
        print()
        print(f"등록 코드: {registration_code}")
        print(f"상태: {status}")
        print()
        print("=" * 60)
        print("이 코드를 PC 등록 프로그램에서 사용하세요.")
        print("=" * 60)
        print()
        return 0
    else:
        print()
        print("[ERROR] 등록 코드 생성에 실패했습니다.")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
