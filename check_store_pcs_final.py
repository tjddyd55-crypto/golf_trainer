#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
store_pcs 테이블 최종 확인 스크립트
- store_name NULL 여부 확인
- status 값 분기 확인
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다.")
    sys.exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # store_pcs 테이블 전체 조회
    cur.execute("""
        SELECT 
            id,
            store_id,
            store_name,
            bay_id,
            bay_name,
            bay_number,
            pc_unique_id,
            pc_name,
            status,
            registered_at
        FROM store_pcs
        ORDER BY registered_at DESC
        LIMIT 20
    """)
    
    rows = cur.fetchall()
    
    print("=" * 80)
    print("store_pcs 테이블 최종 확인 결과")
    print("=" * 80)
    print(f"총 {len(rows)}개 레코드 조회됨\n")
    
    # store_name NULL 확인
    null_store_name_count = 0
    status_counts = {"pending": 0, "active": 0, "inactive": 0, "other": 0}
    
    for row in rows:
        store_name = row.get("store_name")
        status = row.get("status", "").lower()
        
        if store_name is None or store_name == "":
            null_store_name_count += 1
            print(f"❌ [NULL store_name 발견] id={row.get('id')}, store_id={row.get('store_id')}, status={row.get('status')}")
        
        if status == "pending":
            status_counts["pending"] += 1
        elif status == "active":
            status_counts["active"] += 1
        elif status == "inactive":
            status_counts["inactive"] += 1
        else:
            status_counts["other"] += 1
    
    print("\n" + "=" * 80)
    print("요약")
    print("=" * 80)
    print(f"✅ store_name NULL 개수: {null_store_name_count} / {len(rows)}")
    print(f"✅ status 분기:")
    print(f"   - pending: {status_counts['pending']}")
    print(f"   - active: {status_counts['active']}")
    print(f"   - inactive: {status_counts['inactive']}")
    print(f"   - other: {status_counts['other']}")
    
    if null_store_name_count == 0:
        print("\n✅ 모든 레코드의 store_name이 정상적으로 저장되어 있습니다.")
    else:
        print(f"\n❌ {null_store_name_count}개의 레코드에서 store_name이 NULL입니다.")
    
    # 최근 5개 레코드 상세 출력
    print("\n" + "=" * 80)
    print("최근 5개 레코드 상세")
    print("=" * 80)
    for i, row in enumerate(rows[:5], 1):
        print(f"\n[{i}] id={row.get('id')}")
        print(f"    store_id={row.get('store_id')}")
        print(f"    store_name={repr(row.get('store_name'))}")
        print(f"    bay_id={row.get('bay_id')}")
        print(f"    bay_name={row.get('bay_name')}")
        print(f"    bay_number={row.get('bay_number')}")
        print(f"    pc_unique_id={row.get('pc_unique_id')}")
        print(f"    status={row.get('status')}")
        print(f"    registered_at={row.get('registered_at')}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
