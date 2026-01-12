#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
데이터베이스 마이그레이션 실행 스크립트
Railway PostgreSQL에 연결하여 마이그레이션을 실행합니다.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# DATABASE_URL 환경 변수에서 가져오기
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL 환경 변수가 설정되지 않았습니다.")
    print("Railway PostgreSQL 서비스의 Connect 탭에서 Public Network URL을 복사하여 설정하세요.")
    print("\n사용법:")
    print("  set DATABASE_URL=postgresql://user:password@host:port/database")
    print("  python run_migration.py")
    exit(1)

def read_sql_file(filepath):
    """SQL 파일 읽기"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

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
        sql_content = read_sql_file("database_migration_final.sql")
        print("✅ 파일 읽기 완료")
        
        # SQL 실행 (세미콜론으로 구분된 여러 명령 실행)
        print("\n3. 마이그레이션 실행 중...")
        
        # DO 블록과 일반 SQL을 분리하여 실행
        statements = []
        current_statement = ""
        in_do_block = False
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            current_statement += line + '\n'
            
            if 'DO $$' in line:
                in_do_block = True
            elif in_do_block and 'END $$;' in line:
                statements.append(current_statement)
                current_statement = ""
                in_do_block = False
            elif not in_do_block and line.endswith(';'):
                statements.append(current_statement)
                current_statement = ""
        
        # 남은 구문 추가
        if current_statement.strip():
            statements.append(current_statement)
        
        # 각 구문 실행
        for i, statement in enumerate(statements, 1):
            if not statement.strip():
                continue
            
            try:
                print(f"   [{i}/{len(statements)}] 실행 중...")
                cur.execute(statement)
                conn.commit()
                print(f"   ✅ [{i}/{len(statements)}] 완료")
            except Exception as e:
                # 이미 존재하는 컬럼/인덱스는 무시
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"   ⚠️ [{i}/{len(statements)}] 이미 존재함 (무시): {str(e)[:100]}")
                    conn.rollback()
                else:
                    print(f"   ❌ [{i}/{len(statements)}] 오류: {str(e)[:200]}")
                    conn.rollback()
                    raise
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ 마이그레이션 완료!")
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
