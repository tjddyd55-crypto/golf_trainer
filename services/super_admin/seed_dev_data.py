#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
개발 환경용 시드 데이터 생성 스크립트

⚠️ 주의: 이 스크립트는 개발 환경에서만 사용하세요.
운영 환경에서는 절대 실행하지 마세요.

사용법:
    ENVIRONMENT=dev python seed_dev_data.py
"""

import os
import sys

# 공유 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from database import get_db_connection, generate_bay_code

def seed_dev_data():
    """개발 환경용 기본 매장/타석 데이터 생성"""
    
    # 환경변수 확인 (운영 환경에서 실행 방지)
    env = os.environ.get("ENVIRONMENT", "").lower()
    if env not in ["dev", "development", "local"]:
        print("❌ 이 스크립트는 개발 환경에서만 실행할 수 있습니다.")
        print(f"   현재 ENVIRONMENT: {env}")
        print("   ENVIRONMENT=dev python seed_dev_data.py")
        sys.exit(1)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 기본 매장 생성 (gaja)
        cur.execute("SELECT COUNT(*) AS c FROM stores WHERE store_id = %s", ("gaja",))
        row = cur.fetchone()
        
        if not row or row[0] == 0:
            print("[SEED] 기본 매장 생성 중: gaja (가자골프)")
            cur.execute(
                "INSERT INTO stores (store_id, store_name, admin_pw, bays_count) VALUES (%s, %s, %s, %s)",
                ("gaja", "가자골프", "1111", 5),
            )
            
            # 기본 타석 생성 (1~5번)
            print("[SEED] 기본 타석 생성 중: 1~5번")
            for i in range(1, 6):
                bay_id = f"{i:02d}"
                bay_code = generate_bay_code("gaja", bay_id, cur)
                cur.execute(
                    """
                    INSERT INTO bays (store_id, bay_id, status, user_id, last_update, bay_code)
                    VALUES (%s, %s, 'READY', NULL, CURRENT_TIMESTAMP, %s)
                    ON CONFLICT (store_id, bay_id) DO NOTHING
                    """,
                    ("gaja", bay_id, bay_code),
                )
            print("[SEED] ✅ 기본 매장/타석 생성 완료")
        else:
            print("[SEED] 기본 매장이 이미 존재합니다. (gaja)")
            # 기존 매장의 타석 코드 부여 (없는 경우)
            for i in range(1, 6):
                bay_id = f"{i:02d}"
                cur.execute("SELECT bay_code FROM bays WHERE store_id = %s AND bay_id = %s", ("gaja", bay_id))
                existing = cur.fetchone()
                if not existing or not existing[0]:
                    bay_code = generate_bay_code("gaja", bay_id, cur)
                    cur.execute(
                        "UPDATE bays SET bay_code = %s WHERE store_id = %s AND bay_id = %s",
                        (bay_code, "gaja", bay_id)
                    )
            print("[SEED] ✅ 기존 타석 코드 업데이트 완료")
        
        conn.commit()
        print("[SEED] ✅ 시드 데이터 생성 완료")
        
    except Exception as e:
        print(f"[SEED] ❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_dev_data()
