#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""store_pcs 테이블 스키마 확인"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

DATABASE_URL = "postgresql://postgres:iYYgdGvmTCsNAufPMOzGNDBIswuMkcjn@crossover.proxy.rlwy.net:26154/railway"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("store_pcs 테이블 스키마 확인")
    print("=" * 80)
    
    # information_schema에서 컬럼 정보 조회
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'store_pcs'
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    
    print(f"\n총 {len(columns)}개 컬럼\n")
    
    for col in columns:
        col_name = col.get('column_name')
        data_type = col.get('data_type')
        is_nullable = col.get('is_nullable')
        default = col.get('column_default')
        
        nullable_str = "NULL 허용" if is_nullable == 'YES' else "NOT NULL"
        default_str = f" (기본값: {default})" if default else ""
        
        print(f"  {col_name:30} {data_type:20} {nullable_str:15}{default_str}")
    
    # NOT NULL 컬럼만 별도 출력
    print("\n" + "=" * 80)
    print("NOT NULL 컬럼 목록 (필수 포함)")
    print("=" * 80)
    
    for col in columns:
        if col.get('is_nullable') == 'NO':
            print(f"  [필수] {col.get('column_name')} ({col.get('data_type')})")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
