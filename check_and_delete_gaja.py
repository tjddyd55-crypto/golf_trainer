#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Railway PostgreSQL에서 gaja 매장 데이터 확인 및 삭제 스크립트

⚠️ 주의: 이 스크립트는 gaja 매장과 관련된 모든 데이터를 삭제합니다.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# DATABASE_URL 환경 변수에서 가져오기
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("[ERROR] DATABASE_URL environment variable is not set.")
    print("\nUsage:")
    print("  set DATABASE_URL=postgresql://user:password@host:port/database")
    print("  python check_and_delete_gaja.py")
    print("\nOr use Railway PostgreSQL Query Editor:")
    print("  SELECT store_id, store_name, created_at FROM stores WHERE store_id = 'gaja';")
    print("  DELETE FROM stores WHERE store_id = 'gaja';")
    exit(1)

def check_and_delete_gaja():
    """gaja 매장 데이터 확인 및 삭제"""
    try:
        print("=" * 60)
        print("gaja 매장 데이터 확인 및 삭제")
        print("=" * 60)
        
        # 데이터베이스 연결
        print("\n1. Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("[OK] Connection successful")
        
        # gaja 매장 확인
        print("\n2. Checking for gaja store data...")
        cur.execute("SELECT store_id, store_name, created_at FROM stores WHERE store_id = 'gaja'")
        store = cur.fetchone()
        
        if store:
            store_dict = dict(store)
            print(f"[FOUND] gaja store found:")
            print(f"   - store_id: {store_dict.get('store_id')}")
            print(f"   - store_name: {store_dict.get('store_name')}")
            print(f"   - created_at: {store_dict.get('created_at')}")
            
            # 관련 타석 확인
            cur.execute("SELECT COUNT(*) as count FROM bays WHERE store_id = 'gaja'")
            bays_result = cur.fetchone()
            bays_count = bays_result.get('count', 0) if isinstance(bays_result, dict) else bays_result[0]
            print(f"   - Related bays: {bays_count}")
            
            # 관련 store_pcs 확인
            cur.execute("SELECT COUNT(*) as count FROM store_pcs WHERE store_id = 'gaja'")
            pcs_result = cur.fetchone()
            pcs_count = pcs_result.get('count', 0) if isinstance(pcs_result, dict) else pcs_result[0]
            print(f"   - Related PCs: {pcs_count}")
            
            # 관련 샷 데이터 확인
            cur.execute("SELECT COUNT(*) as count FROM shots WHERE store_id = 'gaja'")
            shots_result = cur.fetchone()
            shots_count = shots_result.get('count', 0) if isinstance(shots_result, dict) else shots_result[0]
            print(f"   - Related shots: {shots_count}")
            
            # 삭제 확인
            print(f"\n[WARNING] All data related to gaja store will be deleted:")
            print(f"   - Store: 1")
            print(f"   - Bays: {bays_count}")
            print(f"   - PCs: {pcs_count}")
            print(f"   - Shots: {shots_count}")
            
            confirm = input("\nDelete? (yes/no): ").strip().lower()
            
            if confirm == 'yes':
                print("\n3. Deleting gaja store data...")
                
                # 관련 데이터 삭제 (순서 중요)
                deleted_shots = 0
                deleted_pcs = 0
                deleted_bays = 0
                deleted_stores = 0
                
                # 1. 샷 데이터 삭제
                if shots_count > 0:
                    cur.execute("DELETE FROM shots WHERE store_id = 'gaja'")
                    deleted_shots = cur.rowcount
                    print(f"   [OK] Deleted shots: {deleted_shots}")
                
                # 2. active_sessions 삭제
                cur.execute("DELETE FROM active_sessions WHERE store_id = 'gaja'")
                deleted_sessions = cur.rowcount
                if deleted_sessions > 0:
                    print(f"   [OK] Deleted active sessions: {deleted_sessions}")
                
                # 3. store_pcs 삭제 (store_id 또는 store_name으로)
                cur.execute("DELETE FROM store_pcs WHERE store_id = 'gaja' OR store_name = %s", (store_dict.get('store_name'),))
                deleted_pcs = cur.rowcount
                if deleted_pcs > 0:
                    print(f"   [OK] Deleted PCs: {deleted_pcs}")
                
                # 4. 타석 삭제
                cur.execute("DELETE FROM bays WHERE store_id = 'gaja'")
                deleted_bays = cur.rowcount
                if deleted_bays > 0:
                    print(f"   [OK] Deleted bays: {deleted_bays}")
                
                # 5. 매장 삭제
                cur.execute("DELETE FROM stores WHERE store_id = 'gaja'")
                deleted_stores = cur.rowcount
                
                conn.commit()
                
                print(f"\n[SUCCESS] Deletion complete:")
                print(f"   - Store: {deleted_stores}")
                print(f"   - Bays: {deleted_bays}")
                print(f"   - PCs: {deleted_pcs}")
                print(f"   - Shots: {deleted_shots}")
                
            else:
                print("\n[CANCELLED] Deletion cancelled.")
                conn.rollback()
        else:
            print("[OK] gaja store not found. (Nothing to delete)")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("[OK] Operation complete")
        print("=" * 60)
        
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
    check_and_delete_gaja()
