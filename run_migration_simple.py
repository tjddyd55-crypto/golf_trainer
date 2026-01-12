#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
데이터베이스 마이그레이션 실행 스크립트 (간단 버전)
Railway PostgreSQL에 연결하여 마이그레이션을 실행합니다.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# DATABASE_URL 가져오기 (환경 변수 또는 직접 입력)
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("=" * 60)
    print("Railway PostgreSQL DATABASE_URL이 필요합니다.")
    print("=" * 60)
    print("\n방법 1: 환경 변수 설정")
    print("  set DATABASE_URL=postgresql://user:password@host:port/database")
    print("  python run_migration_simple.py")
    print("\n방법 2: 직접 입력")
    print("  아래에 Railway PostgreSQL의 Public Network URL을 붙여넣으세요.")
    print("  (Railway 대시보드 > PostgreSQL 서비스 > Connect 탭)")
    print("=" * 60)
    DATABASE_URL = input("\nDATABASE_URL: ").strip()
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL이 입력되지 않았습니다.")
        exit(1)

def execute_migration():
    """마이그레이션 실행"""
    try:
        print("=" * 60)
        print("데이터베이스 마이그레이션 시작")
        print("=" * 60)
        
        # 데이터베이스 연결
        print("\n1. 데이터베이스 연결 중...")
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
        cur = conn.cursor()
        print("✅ 연결 성공")
        
        # SQL 파일 읽기
        print("\n2. SQL 파일 읽기 중...")
        with open("database_migration_final.sql", 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print("✅ 파일 읽기 완료")
        
        # SQL 실행
        print("\n3. 마이그레이션 실행 중...")
        
        # DO 블록 단위로 실행
        statements = []
        current = ""
        in_do = False
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            if not stripped or stripped.startswith('--'):
                continue
            
            current += line + '\n'
            
            if 'DO $$' in stripped:
                in_do = True
            elif in_do and 'END $$;' in stripped:
                statements.append(current)
                current = ""
                in_do = False
            elif not in_do and stripped.endswith(';'):
                statements.append(current)
                current = ""
        
        if current.strip():
            statements.append(current)
        
        # 각 구문 실행
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for i, stmt in enumerate(statements, 1):
            if not stmt.strip():
                continue
            
            try:
                print(f"   [{i}/{len(statements)}] 실행 중...", end=' ')
                cur.execute(stmt)
                conn.commit()
                print("✅ 완료")
                success_count += 1
            except psycopg2.errors.DuplicateTable:
                print("⚠️ 이미 존재 (무시)")
                conn.rollback()
                skip_count += 1
            except psycopg2.errors.DuplicateColumn:
                print("⚠️ 이미 존재 (무시)")
                conn.rollback()
                skip_count += 1
            except psycopg2.errors.DuplicateObject:
                print("⚠️ 이미 존재 (무시)")
                conn.rollback()
                skip_count += 1
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    print("⚠️ 이미 존재 (무시)")
                    conn.rollback()
                    skip_count += 1
                else:
                    print(f"❌ 오류: {error_msg[:100]}")
                    conn.rollback()
                    error_count += 1
                    # 치명적 오류가 아니면 계속 진행
                    if "relation" not in error_msg.lower() and "column" not in error_msg.lower():
                        raise
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ 마이그레이션 완료!")
        print(f"   성공: {success_count}, 건너뜀: {skip_count}, 오류: {error_count}")
        print("=" * 60)
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ 데이터베이스 연결 오류: {e}")
        print("\n확인 사항:")
        print("1. DATABASE_URL이 올바른지 확인하세요.")
        print("2. Railway PostgreSQL 서비스가 실행 중인지 확인하세요.")
        print("3. Public Network URL을 사용하고 있는지 확인하세요.")
        exit(1)
    except Exception as e:
        print(f"\n❌ 마이그레이션 오류: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    execute_migration()
