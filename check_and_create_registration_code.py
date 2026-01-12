#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
등록 코드 확인 및 생성 스크립트
"""
import sys
import os

# 공유 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import database

def main():
    print("=" * 60)
    print("등록 코드 확인 및 생성")
    print("=" * 60)
    print()
    
    # 데이터베이스 초기화
    database.init_db()
    
    # 현재 등록 코드 확인
    print("현재 등록 코드 목록:")
    print()
    codes = database.get_all_registration_codes()
    
    if codes:
        active_codes = [c for c in codes if c.get("status") == "ACTIVE"]
        revoked_codes = [c for c in codes if c.get("status") == "REVOKED"]
        
        if active_codes:
            print("[OK] ACTIVE 상태 등록 코드:")
            for code in active_codes:
                print(f"  - {code.get('code')} (생성일: {code.get('created_at')})")
            print()
        else:
            print("[WARNING] ACTIVE 상태 등록 코드가 없습니다.")
            print()
        
        if revoked_codes:
            print(f"[INFO] REVOKED 상태 등록 코드: {len(revoked_codes)}개")
            print()
    else:
        print("[WARNING] 등록 코드가 없습니다.")
        print()
    
    # ACTIVE 코드가 없으면 생성
    active_codes = [c for c in codes if c.get("status") == "ACTIVE"] if codes else []
    
    if not active_codes:
        print("ACTIVE 상태 등록 코드 생성 중...")
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
    else:
        print("=" * 60)
        print("[OK] 이미 ACTIVE 상태 등록 코드가 있습니다.")
        print("=" * 60)
        print()
        print("사용 가능한 등록 코드:")
        for code in active_codes:
            print(f"  - {code.get('code')}")
        print()
        return 0

if __name__ == "__main__":
    sys.exit(main())
