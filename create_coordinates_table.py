# -*- coding: utf-8 -*-
"""
Railway PostgreSQL에 coordinates 테이블 생성 스크립트
"""
import sys
import os

# shared 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared import database

def main():
    """coordinates 테이블 생성"""
    print("=" * 40)
    print("coordinates 테이블 생성")
    print("=" * 40)
    print()
    
    try:
        conn = database.get_db_connection()
        cur = conn.cursor()
        
        # 테이블 생성
        print("테이블 생성 중...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS coordinates (
                id SERIAL PRIMARY KEY,
                brand VARCHAR(50) NOT NULL,
                resolution VARCHAR(20) NOT NULL,
                version INTEGER NOT NULL,
                filename VARCHAR(100) NOT NULL,
                payload JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (brand, resolution, version)
            )
        """)
        
        # 인덱스 생성
        print("인덱스 생성 중...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_coordinates_brand ON coordinates(brand)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_coordinates_brand_filename ON coordinates(brand, filename)")
        
        conn.commit()
        print()
        print("[성공] coordinates 테이블이 생성되었습니다.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print()
        print(f"[오류] 테이블 생성 중 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
