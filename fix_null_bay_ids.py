#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
기존 bay_id가 None인 데이터 처리 스크립트

사용법:
    python fix_null_bay_ids.py [DATABASE_URL]
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DATABASE_URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DATABASE_URL", "postgresql://postgres:iYYgdGvmTCsNAufPMOzGNDBIswuMkcjn@crossover.proxy.rlwy.net:26154/railway")

try:
    print("=" * 80)
    print("기존 bay_id가 None인 데이터 확인 및 처리")
    print("=" * 80)
    
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # bay_id가 NULL인 active 타석 확인
    print("\n1. bay_id가 NULL인 active 타석 확인:")
    print("-" * 80)
    cur.execute("""
        SELECT 
            pc_unique_id,
            store_id,
            store_name,
            bay_id,
            bay_name,
            pc_name,
            status
        FROM store_pcs
        WHERE status = 'active'
          AND (bay_id IS NULL OR bay_id = '')
        ORDER BY store_id, pc_unique_id
    """)
    
    null_bays = cur.fetchall()
    print(f"총 {len(null_bays)}개 발견\n")
    
    if null_bays:
        for pc in null_bays:
            print(f"  - pc_unique_id: {pc.get('pc_unique_id')}")
            print(f"    store_id: {pc.get('store_id')}")
            print(f"    store_name: {pc.get('store_name')}")
            print(f"    bay_id: {pc.get('bay_id')} (NULL)")
            print(f"    bay_name: {pc.get('bay_name')}")
            print(f"    pc_name: {pc.get('pc_name')}")
            print()
        
        print("\n⚠️  이 타석들은 관리자 화면에서 bay_id를 설정해야 합니다.")
        print("   또는 아래 SQL로 직접 수정할 수 있습니다:\n")
        
        for pc in null_bays:
            store_id = pc.get('store_id')
            bay_name = pc.get('bay_name', '')
            pc_unique_id = pc.get('pc_unique_id')
            
            # bay_name에서 숫자 추출 시도
            import re
            match = re.search(r'(\d+)', bay_name)
            if match:
                suggested_bay_id = int(match.group(1))
                print(f"  -- {store_id} / {bay_name}")
                print(f"  UPDATE store_pcs")
                print(f"  SET bay_id = '{suggested_bay_id}'")
                print(f"  WHERE pc_unique_id = '{pc_unique_id}';")
                print()
            else:
                print(f"  -- {store_id} / {bay_name} (수동 설정 필요)")
                print(f"  UPDATE store_pcs")
                print(f"  SET bay_id = '1'  -- 적절한 번호로 변경 필요")
                print(f"  WHERE pc_unique_id = '{pc_unique_id}';")
                print()
    else:
        print("  ✅ bay_id가 NULL인 active 타석이 없습니다.")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("[OK] 확인 완료")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ 오류: {e}")
    import traceback
    traceback.print_exc()
