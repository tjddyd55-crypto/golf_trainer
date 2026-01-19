#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
모든 매장과 타석 확인
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DATABASE_URL = "postgresql://postgres:iYYgdGvmTCsNAufPMOzGNDBIswuMkcjn@crossover.proxy.rlwy.net:26154/railway"

try:
    print("=" * 80)
    print("모든 매장 및 타석 확인")
    print("=" * 80)
    
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 모든 매장 조회
    print("\n1. 모든 매장 목록:")
    print("-" * 80)
    cur.execute("SELECT store_id, store_name FROM stores ORDER BY store_id")
    stores = cur.fetchall()
    
    for store in stores:
        store_id = store.get('store_id')
        store_name = store.get('store_name')
        print(f"\n  매장: {store_id} ({store_name})")
        
        # 해당 매장의 store_pcs 확인
        cur.execute("""
            SELECT
                bay_id,
                bay_name,
                status,
                usage_end_date,
                pc_name
            FROM store_pcs
            WHERE store_id = %s
            ORDER BY bay_id
        """, (store_id,))
        
        pcs = cur.fetchall()
        print(f"    총 타석: {len(pcs)}개")
        
        for pc in pcs:
            print(f"      - bay_id: {pc.get('bay_id')}, bay_name: {pc.get('bay_name')}, status: {pc.get('status')}")
        
        # 활성 타석만
        cur.execute("""
            SELECT COUNT(*) as count
            FROM store_pcs
            WHERE store_id = %s
              AND status = 'active'
              AND bay_id IS NOT NULL
              AND bay_id != ''
              AND (usage_end_date IS NULL OR usage_end_date::date >= CURRENT_DATE)
        """, (store_id,))
        
        active_count = cur.fetchone().get('count', 0)
        print(f"    활성 타석: {active_count}개")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("[OK] 확인 완료")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ 오류: {e}")
    import traceback
    traceback.print_exc()
