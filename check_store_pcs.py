#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Railway PostgreSQL에서 store_pcs 타석 데이터 확인 스크립트

STEP 1: DB 실체 확인

Usage:
    python check_store_pcs.py [DATABASE_URL]
    
    또는 환경 변수:
    set DATABASE_URL=postgresql://user:password@host:port/database
    python check_store_pcs.py
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# UTF-8 출력 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# DATABASE_URL 확인 (명령줄 인자 또는 환경 변수)
DATABASE_URL = None

# 1. 명령줄 인자 확인
if len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]

# 2. 환경 변수 확인
if not DATABASE_URL:
    DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL이 설정되지 않았습니다.")
    print("\n사용 방법:")
    print("  1. 명령줄 인자로 전달:")
    print("     python check_store_pcs.py postgresql://user:password@host:port/database")
    print("\n  2. 환경 변수로 설정:")
    print("     set DATABASE_URL=postgresql://user:password@host:port/database")
    print("     python check_store_pcs.py")
    print("\n  3. Railway PostgreSQL Query Editor 사용:")
    print("     Railway 대시보드 → PostgreSQL → Query 탭")
    print("     아래 쿼리 실행:")
    print("\n     SELECT bay_id, bay_name, status, usage_end_date")
    print("     FROM store_pcs")
    print("     WHERE store_id = 'testid2'")
    print("       AND status = 'active'")
    print("       AND bay_id IS NOT NULL")
    print("       AND bay_id != '';")
    exit(1)

def check_store_pcs(store_id):
    """store_pcs 타석 데이터 확인"""
    try:
        print("=" * 80)
        print(f"store_pcs 타석 데이터 확인: store_id = '{store_id}'")
        print("=" * 80)
        
        # 데이터베이스 연결
        print("\n1. Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("[OK] Connection successful")
        
        # 쿼리 1: 전체 store_pcs 확인
        print(f"\n2. [쿼리 1] 전체 store_pcs 확인:")
        print("-" * 80)
        cur.execute("""
            SELECT
                store_id,
                bay_id,
                bay_name,
                status,
                usage_end_date,
                pc_name
            FROM store_pcs
            WHERE store_id = %s
            ORDER BY bay_id
        """, (store_id,))
        
        all_pcs = cur.fetchall()
        print(f"총 {len(all_pcs)}개 타석 발견\n")
        
        if all_pcs:
            for pc in all_pcs:
                print(f"  - bay_id: {pc.get('bay_id')}")
                print(f"    bay_name: {pc.get('bay_name')}")
                print(f"    status: {pc.get('status')}")
                print(f"    usage_end_date: {pc.get('usage_end_date')}")
                print(f"    pc_name: {pc.get('pc_name')}")
                print()
        else:
            print("  [결과] 타석이 없습니다.")
        
        # 쿼리 2: 활성 타석만 확인 (get_bays()와 동일 조건)
        print(f"\n3. [쿼리 2] 활성 타석만 확인 (get_bays() 조건):")
        print("-" * 80)
        cur.execute("""
            SELECT
                bay_id,
                bay_name,
                status,
                usage_end_date,
                pc_name
            FROM store_pcs
            WHERE store_id = %s
              AND status = 'active'
              AND bay_id IS NOT NULL
              AND bay_id != ''
              AND (usage_end_date IS NULL OR usage_end_date::date >= CURRENT_DATE)
            ORDER BY bay_id
        """, (store_id,))
        
        active_pcs = cur.fetchall()
        print(f"활성 타석: {len(active_pcs)}개\n")
        
        if active_pcs:
            for pc in active_pcs:
                print(f"  ✅ bay_id: {pc.get('bay_id')}")
                print(f"     bay_name: {pc.get('bay_name')}")
                print(f"     status: {pc.get('status')}")
                print(f"     usage_end_date: {pc.get('usage_end_date')}")
                print(f"     pc_name: {pc.get('pc_name')}")
                print()
        else:
            print("  [결과] 활성 타석이 없습니다.")
        
        # 결과 해석
        print("\n" + "=" * 80)
        print("📊 결과 해석:")
        print("=" * 80)
        
        if len(active_pcs) >= 2:
            print("✅ 2개 이상 활성 타석 발견 → DB는 정상")
            print("   → 문제는 애플리케이션 로직 (STEP 2로 진행)")
        elif len(active_pcs) == 1:
            print("❌ 1개만 활성 타석 발견 → DB 문제 확정")
            print("   → 관리자 승인 단계에서 1개만 active 상태")
            print("   → 해결: 관리자 화면에서 다른 타석도 승인 상태 확인")
        else:
            print("⚠️ 활성 타석 없음")
            print("   → 관리자 화면에서 타석 승인 필요")
        
        # 매장 정보도 확인
        print(f"\n4. 매장 정보 확인:")
        print("-" * 80)
        cur.execute("SELECT store_id, store_name FROM stores WHERE store_id = %s", (store_id,))
        store = cur.fetchone()
        if store:
            print(f"  store_id: {store.get('store_id')}")
            print(f"  store_name: {store.get('store_name')}")
        else:
            print(f"  [경고] 매장이 존재하지 않습니다: {store_id}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("[OK] 확인 완료")
        print("=" * 80)
        
        return len(active_pcs)
        
    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Database connection error: {e}")
        print("\nPlease check:")
        print("1. DATABASE_URL is correct")
        print("2. Railway PostgreSQL service is running")
        exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    # 문제되는 store_id들 확인
    store_ids = ["testid2", "가자스크린골프테스트2"]
    
    for store_id in store_ids:
        try:
            check_store_pcs(store_id)
            print("\n\n")
        except Exception as e:
            print(f"\n[ERROR] {store_id} 확인 중 오류: {e}")
            print("\n\n")
