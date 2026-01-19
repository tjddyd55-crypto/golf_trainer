#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DB에서 store_pcs 테이블 확인"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

DATABASE_URL = "postgresql://postgres:iYYgdGvmTCsNAufPMOzGNDBIswuMkcjn@crossover.proxy.rlwy.net:26154/railway"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("store_pcs 테이블 전체 조회")
    print("=" * 80)
    
    # 전체 조회
    cur.execute("""
        SELECT 
            pc_unique_id, 
            store_id, 
            store_name, 
            bay_id, 
            bay_number, 
            bay_name, 
            status, 
            registered_at
        FROM store_pcs 
        ORDER BY registered_at DESC
    """)
    
    rows = cur.fetchall()
    
    print(f"\n총 {len(rows)}개 레코드\n")
    
    for i, row in enumerate(rows, 1):
        print(f"[{i}]")
        print(f"  pc_unique_id: {row.get('pc_unique_id')}")
        print(f"  store_id: {row.get('store_id')}")
        print(f"  store_name: {row.get('store_name')} {'❌ NULL' if row.get('store_name') is None else '✅'}")
        print(f"  bay_id: {row.get('bay_id')}")
        print(f"  bay_number: {row.get('bay_number')}")
        print(f"  bay_name: {row.get('bay_name')}")
        print(f"  status: {row.get('status')}")
        print(f"  registered_at: {row.get('registered_at')}")
        print()
    
    # TESTID 매장만 조회
    print("=" * 80)
    print("TESTID 매장 PC 목록")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            pc_unique_id, 
            store_id, 
            store_name, 
            bay_id, 
            bay_number, 
            bay_name, 
            status, 
            registered_at
        FROM store_pcs 
        WHERE store_id = 'TESTID'
        ORDER BY registered_at DESC
    """)
    
    testid_rows = cur.fetchall()
    
    print(f"\nTESTID 매장: {len(testid_rows)}개 레코드\n")
    
    for i, row in enumerate(testid_rows, 1):
        print(f"[{i}]")
        print(f"  pc_unique_id: {row.get('pc_unique_id')}")
        print(f"  store_id: {row.get('store_id')}")
        print(f"  store_name: {row.get('store_name')} {'❌ NULL' if row.get('store_name') is None else '✅'}")
        print(f"  bay_id: {row.get('bay_id')}")
        print(f"  bay_number: {row.get('bay_number')}")
        print(f"  bay_name: {row.get('bay_name')}")
        print(f"  status: {row.get('status')}")
        print(f"  registered_at: {row.get('registered_at')}")
        print()
    
    # stores 테이블에서 TESTID 매장 정보 확인
    print("=" * 80)
    print("stores 테이블 - TESTID 매장 정보")
    print("=" * 80)
    
    cur.execute("""
        SELECT store_id, store_name, bays_count, status
        FROM stores
        WHERE store_id = 'TESTID'
    """)
    
    store_info = cur.fetchone()
    
    if store_info:
        print(f"store_id: {store_info.get('store_id')}")
        print(f"store_name: {store_info.get('store_name')}")
        print(f"bays_count: {store_info.get('bays_count')}")
        print(f"status: {store_info.get('status')}")
    else:
        print("TESTID 매장이 stores 테이블에 없습니다.")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
