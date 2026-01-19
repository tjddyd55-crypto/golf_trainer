#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""store_pcs 테이블 DB 레벨 문제 확인 (트리거, RULE, DEFAULT)"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

DATABASE_URL = "postgresql://postgres:iYYgdGvmTCsNAufPMOzGNDBIswuMkcjn@crossover.proxy.rlwy.net:26154/railway"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("1. store_pcs 테이블 트리거 확인")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            tgname as trigger_name,
            tgtype::int as trigger_type,
            tgrelid::regclass as table_name,
            CASE 
                WHEN tgtype::int & 2 = 2 THEN 'BEFORE'
                WHEN tgtype::int & 4 = 4 THEN 'AFTER'
                ELSE 'UNKNOWN'
            END as timing,
            CASE 
                WHEN tgtype::int & 8 = 8 THEN 'INSERT'
                WHEN tgtype::int & 16 = 16 THEN 'DELETE'
                WHEN tgtype::int & 32 = 32 THEN 'UPDATE'
                ELSE 'OTHER'
            END as event
        FROM pg_trigger
        WHERE tgrelid = 'store_pcs'::regclass
          AND NOT tgisinternal
    """)
    
    triggers = cur.fetchall()
    
    if triggers:
        print(f"\n총 {len(triggers)}개 트리거 발견:\n")
        for t in triggers:
            print(f"  트리거명: {t.get('trigger_name')}")
            print(f"  타입: {t.get('trigger_type')}")
            print(f"  타이밍: {t.get('timing')}")
            print(f"  이벤트: {t.get('event')}")
            print()
    else:
        print("\n  [OK] 트리거 없음\n")
    
    print("=" * 80)
    print("2. store_pcs 테이블 RULE 확인")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            rulename,
            definition
        FROM pg_rules
        WHERE tablename = 'store_pcs'
    """)
    
    rules = cur.fetchall()
    
    if rules:
        print(f"\n총 {len(rules)}개 RULE 발견:\n")
        for r in rules:
            print(f"  RULE명: {r.get('rulename')}")
            print(f"  정의: {r.get('definition')}")
            print()
    else:
        print("\n  [OK] RULE 없음\n")
    
    print("=" * 80)
    print("3. store_name 컬럼 DEFAULT 값 확인")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            column_name,
            column_default,
            is_nullable,
            data_type
        FROM information_schema.columns
        WHERE table_name = 'store_pcs'
          AND column_name = 'store_name'
    """)
    
    column_info = cur.fetchone()
    
    if column_info:
        print(f"\n  컬럼명: {column_info.get('column_name')}")
        print(f"  데이터 타입: {column_info.get('data_type')}")
        print(f"  NULL 허용: {column_info.get('is_nullable')}")
        default_val = column_info.get('column_default')
        if default_val:
            print(f"  DEFAULT 값: {default_val}")
        else:
            print(f"  DEFAULT 값: 없음 (NULL)")
        print()
    else:
        print("\n  ❌ store_name 컬럼을 찾을 수 없음\n")
    
    print("=" * 80)
    print("4. DB 콘솔 직접 INSERT 테스트")
    print("=" * 80)
    
    # 테스트용 INSERT 실행
    test_store_name = "DIRECT_TEST_DB_INSERT"
    test_store_id = "TESTID"
    
    print(f"\n  테스트 INSERT 실행:")
    print(f"    store_name = '{test_store_name}'")
    print(f"    store_id = '{test_store_id}'")
    print()
    
    try:
        # 기존 테스트 레코드 삭제 (있을 경우)
        cur.execute("""
            DELETE FROM store_pcs 
            WHERE store_id = %s AND store_name = %s
        """, (test_store_id, test_store_name))
        
        # 직접 INSERT 실행 (필수 NOT NULL 컬럼 포함)
        cur.execute("""
            INSERT INTO store_pcs (
                store_name, 
                store_id, 
                bay_name, 
                pc_name, 
                pc_unique_id, 
                bay_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            test_store_name, 
            test_store_id, 
            'TEST_BAY', 
            'TEST_PC', 
            'TEST_PC_UNIQUE_ID', 
            'TEST_BAY_ID'
        ))
        
        conn.commit()
        
        # INSERT 결과 확인
        cur.execute("""
            SELECT store_name, store_id
            FROM store_pcs
            WHERE store_id = %s AND store_name = %s
        """, (test_store_id, test_store_name))
        
        result = cur.fetchone()
        
        if result:
            saved_store_name = result.get('store_name')
            print(f"  [OK] INSERT 성공")
            print(f"  저장된 store_name: '{saved_store_name}'")
            
            if saved_store_name is None:
                print(f"  [ERROR] store_name이 NULL로 저장됨 (DB 레벨 문제 확정)")
            elif saved_store_name == test_store_name:
                print(f"  [OK] store_name이 정상적으로 저장됨")
            else:
                print(f"  [WARNING] store_name이 예상과 다름: '{saved_store_name}'")
        else:
            print(f"  [ERROR] INSERT 후 조회 실패 (레코드 없음)")
        
        # 테스트 레코드 정리
        cur.execute("""
            DELETE FROM store_pcs 
            WHERE store_id = %s AND store_name = %s AND bay_name = 'TEST_BAY'
        """, (test_store_id, test_store_name))
        conn.commit()
        print(f"  테스트 레코드 정리 완료")
        
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] INSERT 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("확인 완료")
    print("=" * 80)
    
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
