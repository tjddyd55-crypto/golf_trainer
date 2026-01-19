#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bay_id 정규화 작업 스크립트

1. NULL bay_id 확인
2. 앞자리 0 포함 bay_id 정규화 (03 → 3)
3. 중복 체크
4. DB 보호 장치 적용
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import re

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DATABASE_URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DATABASE_URL", "postgresql://postgres:iYYgdGvmTCsNAufPMOzGNDBIswuMkcjn@crossover.proxy.rlwy.net:26154/railway")

def normalize_bay_ids():
    """bay_id 정규화 작업"""
    try:
        print("=" * 80)
        print("bay_id 정규화 작업")
        print("=" * 80)
        
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=30)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1️⃣ 현재 문제 데이터 확인 (NULL + 0패딩)
        print("\n1. 현재 문제 데이터 확인 (NULL + 0패딩):")
        print("-" * 80)
        cur.execute("""
            SELECT store_id, bay_id, bay_name, status, pc_unique_id
            FROM store_pcs
            WHERE status = 'active'
              AND (bay_id IS NULL OR bay_id ~ '^0+[0-9]+$')
            ORDER BY store_id, bay_name
        """)
        
        problem_pcs = cur.fetchall()
        print(f"총 {len(problem_pcs)}개 발견\n")
        
        if problem_pcs:
            for pc in problem_pcs:
                print(f"  - store_id: {pc.get('store_id')}")
                print(f"    bay_id: {pc.get('bay_id')} ({'NULL' if pc.get('bay_id') is None else '0패딩'})")
                print(f"    bay_name: {pc.get('bay_name')}")
                print(f"    pc_unique_id: {pc.get('pc_unique_id')}")
                print()
        else:
            print("  ✅ 문제 데이터 없음")
        
        # 2️⃣ NULL bay_id 임시 목록 확인
        print("\n2. NULL bay_id 목록 (관리자 매핑용):")
        print("-" * 80)
        cur.execute("""
            SELECT store_id, bay_name, pc_unique_id
            FROM store_pcs
            WHERE status = 'active'
              AND bay_id IS NULL
            ORDER BY store_id, bay_name
        """)
        
        null_pcs = cur.fetchall()
        print(f"총 {len(null_pcs)}개\n")
        
        if null_pcs:
            for pc in null_pcs:
                print(f"  - store_id: {pc.get('store_id')}")
                print(f"    bay_name: {pc.get('bay_name')}")
                print(f"    pc_unique_id: {pc.get('pc_unique_id')}")
                print()
            
            print("⚠️  NULL bay_id는 관리자가 직접 설정해야 합니다.")
            print("   아래 SQL로 수정하거나 관리자 화면에서 수정하세요:\n")
            
            for pc in null_pcs:
                store_id = pc.get('store_id')
                bay_name = pc.get('bay_name')
                pc_unique_id = pc.get('pc_unique_id')
                
                # bay_name에서 숫자 추출 시도
                match = re.search(r'(\d+)', bay_name)
                if match:
                    suggested_bay_id = int(match.group(1))
                    print(f"  -- {store_id} / {bay_name} → bay_id={suggested_bay_id} (추정)")
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
        
        # NULL bay_id 자동 수정 (능동집테스트는 2번으로 설정, 03번이 이미 있으므로)
        if null_pcs:
            print("\n3. NULL bay_id 자동 수정:")
            print("-" * 80)
            
            for pc in null_pcs:
                store_id = pc.get('store_id')
                bay_name = pc.get('bay_name')
                pc_unique_id = pc.get('pc_unique_id')
                
                # 능동집테스트는 2번으로 설정 (03번이 이미 있으므로)
                if bay_name == '능동집테스트' and store_id == 'TESTID2':
                    suggested_bay_id = 2
                    print(f"  {store_id} / {bay_name} → bay_id={suggested_bay_id} (자동 설정)")
                else:
                    # bay_name에서 숫자 추출 시도
                    match = re.search(r'(\d+)', bay_name)
                    if match:
                        suggested_bay_id = int(match.group(1))
                        print(f"  {store_id} / {bay_name} → bay_id={suggested_bay_id} (추정)")
                    else:
                        print(f"  {store_id} / {bay_name} → 수동 설정 필요 (숫자 없음)")
                        continue
                
                # 중복 체크 (bay_id는 TEXT이므로 문자열로 비교)
                cur.execute("""
                    SELECT 1
                    FROM store_pcs
                    WHERE store_id = %s
                      AND bay_id = %s
                      AND status = 'active'
                      AND pc_unique_id != %s
                    LIMIT 1
                """, (store_id, str(suggested_bay_id), pc_unique_id))
                
                if cur.fetchone():
                    print(f"    ⚠️  중복! bay_id={suggested_bay_id}는 이미 사용 중입니다. 건너뜁니다.")
                    continue
                
                cur.execute("""
                    UPDATE store_pcs
                    SET bay_id = %s
                    WHERE pc_unique_id = %s
                """, (str(suggested_bay_id), pc_unique_id))
                print(f"    ✅ 수정 완료")
            
            conn.commit()
            print("\n✅ NULL bay_id 수정 완료")
        
        # 4️⃣ 앞자리 0 포함 bay_id 정규화
        print("\n4. 앞자리 0 포함 bay_id 정규화 (03 → 3):")
        print("-" * 80)
        
        cur.execute("""
            SELECT store_id, bay_id, bay_name, pc_unique_id
            FROM store_pcs
            WHERE status = 'active'
              AND bay_id ~ '^0+[0-9]+$'
            ORDER BY store_id, bay_id
        """)
        
        padded_pcs = cur.fetchall()
        print(f"총 {len(padded_pcs)}개 발견\n")
        
        if padded_pcs:
            for pc in padded_pcs:
                old_bay_id = pc.get('bay_id')
                new_bay_id = int(old_bay_id)
                print(f"  {pc.get('store_id')} / {pc.get('bay_name')}: '{old_bay_id}' → {new_bay_id}")
            
            print("\n  정규화 실행 중...")
            
            # PostgreSQL에서 직접 정규화
            cur.execute("""
                UPDATE store_pcs
                SET bay_id = CAST(bay_id AS INTEGER)::TEXT
                WHERE status = 'active'
                  AND bay_id ~ '^0+[0-9]+$'
            """)
            
            updated_count = cur.rowcount
            conn.commit()
            print(f"  ✅ {updated_count}개 정규화 완료")
        else:
            print("  ✅ 정규화할 데이터 없음")
        
        # 5️⃣ 정규화 결과 검증
        print("\n5. 정규화 결과 검증:")
        print("-" * 80)
        cur.execute("""
            SELECT store_id, bay_id, bay_name, status
            FROM store_pcs
            WHERE status = 'active'
            ORDER BY store_id, CAST(bay_id AS INTEGER)
        """)
        
        all_active = cur.fetchall()
        print(f"총 {len(all_active)}개 active 타석\n")
        
        has_null = False
        has_padding = False
        
        for pc in all_active:
            bay_id = pc.get('bay_id')
            if bay_id is None:
                has_null = True
                print(f"  ❌ NULL: {pc.get('store_id')} / {pc.get('bay_name')}")
            elif re.match(r'^0+[0-9]+$', bay_id):
                has_padding = True
                print(f"  ❌ 0패딩: {pc.get('store_id')} / {pc.get('bay_name')} / bay_id={bay_id}")
            else:
                print(f"  ✅ {pc.get('store_id')} / bay_id={bay_id} / {pc.get('bay_name')}")
        
        if not has_null and not has_padding:
            print("\n  ✅ 모든 bay_id가 정규화되었습니다.")
        else:
            print("\n  ⚠️  일부 bay_id가 아직 정규화되지 않았습니다.")
        
        # 6️⃣ 중복 최종 점검
        print("\n6. 중복 최종 점검:")
        print("-" * 80)
        cur.execute("""
            SELECT store_id, bay_id, COUNT(*) as count
            FROM store_pcs
            WHERE status = 'active'
              AND bay_id IS NOT NULL
            GROUP BY store_id, bay_id
            HAVING COUNT(*) > 1
            ORDER BY store_id, bay_id
        """)
        
        duplicates = cur.fetchall()
        
        if duplicates:
            print(f"  ❌ 중복 발견: {len(duplicates)}개\n")
            for dup in duplicates:
                print(f"    store_id: {dup.get('store_id')}, bay_id: {dup.get('bay_id')}, count: {dup.get('count')}")
            
            print("\n  ⚠️  중복을 해결해야 합니다. 관리자가 하나를 선택해야 합니다.")
        else:
            print("  ✅ 중복 없음")
        
        # 7️⃣ DB 보호 장치 적용
        print("\n7. DB 보호 장치 적용:")
        print("-" * 80)
        
        # UNIQUE INDEX (이미 코드에 추가됨, 확인만)
        try:
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_store_bay_id_active
                ON store_pcs (store_id, bay_id)
                WHERE status = 'active' AND bay_id IS NOT NULL
            """)
            print("  ✅ UNIQUE INDEX 생성 완료")
        except Exception as e:
            print(f"  ⚠️  UNIQUE INDEX 생성 실패 (이미 존재할 수 있음): {e}")
        
        # NOT NULL 제약조건은 기존 데이터가 NULL일 수 있으므로
        # 모든 데이터 정리 후에만 적용 가능
        if not has_null:
            try:
                cur.execute("""
                    ALTER TABLE store_pcs
                    ALTER COLUMN bay_id SET NOT NULL
                """)
                conn.commit()
                print("  ✅ NOT NULL 제약조건 적용 완료")
            except Exception as e:
                print(f"  ⚠️  NOT NULL 제약조건 적용 실패: {e}")
        else:
            print("  ⏭️  NOT NULL 제약조건 적용 건너뜀 (NULL 데이터가 있음)")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("[OK] 정규화 작업 완료")
        print("=" * 80)
        
        if duplicates:
            print("\n⚠️  경고: 중복이 발견되었습니다. 수동으로 해결하세요.")
        if has_null:
            print("\n⚠️  경고: NULL bay_id가 남아있습니다. 수동으로 수정하세요.")
        
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    normalize_bay_ids()
