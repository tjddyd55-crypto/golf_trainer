# -*- coding: utf-8 -*-
"""
좌표 데이터 확인 스크립트
"""
import sys
import os

# shared 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared import database

def main():
    """좌표 데이터 확인"""
    print("=" * 60)
    print("좌표 데이터 확인")
    print("=" * 60)
    print()
    
    try:
        conn = database.get_db_connection()
        cur = conn.cursor()
        
        # 1. 전체 좌표 데이터 개수 확인
        print("1️⃣ 전체 좌표 데이터 개수 확인")
        print("-" * 60)
        cur.execute("SELECT count(*) FROM coordinates")
        total_count = cur.fetchone()[0]
        print(f"전체 좌표 데이터 개수: {total_count}개")
        print()
        
        # 2. 브랜드별 저장된 개수 확인
        print("2️⃣ 브랜드별 저장된 개수 확인")
        print("-" * 60)
        cur.execute("""
            SELECT brand, count(*) 
            FROM coordinates 
            GROUP BY brand
            ORDER BY brand
        """)
        brand_counts = cur.fetchall()
        if brand_counts:
            for brand, count in brand_counts:
                print(f"  {brand}: {count}개")
        else:
            print("  (저장된 데이터 없음)")
        print()
        
        # 3. 저장된 데이터 목록 상세 조회
        print("3️⃣ 저장된 데이터 목록 상세 조회")
        print("-" * 60)
        cur.execute("""
            SELECT id, brand, resolution, version, filename, created_at 
            FROM coordinates 
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        
        if rows:
            print(f"{'ID':<5} {'Brand':<15} {'Resolution':<15} {'Version':<10} {'Filename':<35} {'Created At':<20}")
            print("-" * 100)
            for row in rows:
                id_val, brand, resolution, version, filename, created_at = row
                created_str = str(created_at)[:19] if created_at else "N/A"
                print(f"{id_val:<5} {brand:<15} {resolution:<15} {version:<10} {filename:<35} {created_str:<20}")
        else:
            print("  (저장된 데이터 없음)")
        print()
        
        cur.close()
        conn.close()
        
        print("=" * 60)
        print("조회 완료!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print(f"[ERROR] 데이터 조회 중 오류가 발생했습니다: {e}")
        print()
        print("데이터베이스 연결 정보 확인:")
        print(f"  DATABASE_URL 환경 변수가 설정되어 있는지 확인하세요.")
        print(f"  또는 shared/database.py의 기본 연결 정보를 확인하세요.")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
