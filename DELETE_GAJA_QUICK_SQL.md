# gaja 매장 삭제 SQL (Railway Query Editor 복사용)

Railway 대시보드에서 **Query Editor**를 열고 아래 SQL을 순서대로 실행하세요.

---

## 1단계: gaja 매장 확인

```sql
SELECT store_id, store_name, created_at 
FROM stores 
WHERE store_id = 'gaja';
```

**결과 확인**:
- 데이터가 있으면 → 삭제 진행
- 데이터가 없으면 → 이미 삭제됨 (작업 완료)

---

## 2단계: 관련 데이터 확인 (선택사항)

```sql
-- 관련 타석 수
SELECT COUNT(*) as bays_count FROM bays WHERE store_id = 'gaja';

-- 관련 PC 수
SELECT COUNT(*) as pcs_count FROM store_pcs WHERE store_id = 'gaja' OR store_name = (SELECT store_name FROM stores WHERE store_id = 'gaja');

-- 관련 샷 데이터 수
SELECT COUNT(*) as shots_count FROM shots WHERE store_id = 'gaja';
```

---

## 3단계: gaja 매장 및 관련 데이터 삭제

**⚠️ 주의: 삭제 후 복구 불가능합니다!**

아래 SQL을 **순서대로** 실행하세요:

```sql
-- 1. 샷 데이터 삭제
DELETE FROM shots WHERE store_id = 'gaja';

-- 2. 활성 세션 삭제
DELETE FROM active_sessions WHERE store_id = 'gaja';

-- 3. PC 데이터 삭제 (store_name도 확인)
DELETE FROM store_pcs 
WHERE store_id = 'gaja' 
   OR store_name = (SELECT store_name FROM stores WHERE store_id = 'gaja');

-- 4. 타석 삭제
DELETE FROM bays WHERE store_id = 'gaja';

-- 5. 매장 삭제
DELETE FROM stores WHERE store_id = 'gaja';
```

---

## 4단계: 삭제 확인

```sql
-- gaja 매장이 삭제되었는지 확인
SELECT store_id, store_name 
FROM stores 
WHERE store_id = 'gaja';
```

**결과**: 0 rows 나와야 정상입니다.

---

## Railway Query Editor 사용 방법

1. **Railway 대시보드 접속**
   - https://railway.app 접속
   - GitHub로 로그인

2. **PostgreSQL 서비스 선택**
   - 프로젝트에서 PostgreSQL 서비스 찾기
   - PostgreSQL 서비스 카드 클릭

3. **Query 탭 클릭**
   - 서비스 상세 페이지에서 **"Query"** 탭 클릭
   - 또는 상단 메뉴에서 **"Query"** 선택

4. **SQL 실행**
   - 위 SQL을 복사해서 붙여넣기
   - **"Run Query"** 버튼 클릭
   - 결과 확인

---

## ⚠️ 주의사항

1. **삭제 순서 중요**: 외래 키 제약 때문에 위 순서를 반드시 따라야 합니다.
2. **삭제 전 확인**: 1단계에서 gaja 매장이 실제로 존재하는지 확인하세요.
3. **백업 권장**: 중요한 데이터라면 삭제 전 백업을 권장합니다.

---

## 문제 해결

### "relation does not exist" 오류

```
ERROR: relation "stores" does not exist
```

**해결**: 올바른 PostgreSQL 서비스에 연결되어 있는지 확인하세요.

### "permission denied" 오류

```
ERROR: permission denied for table stores
```

**해결**: Railway PostgreSQL 사용자는 일반적으로 모든 권한이 있습니다. 오류가 계속되면 Railway 지원팀에 문의하세요.

---

## 빠른 실행 (전체 복사)

아래 블록을 한 번에 복사해서 실행할 수도 있습니다:

```sql
-- gaja 매장 삭제 (전체)
BEGIN;

DELETE FROM shots WHERE store_id = 'gaja';
DELETE FROM active_sessions WHERE store_id = 'gaja';
DELETE FROM store_pcs WHERE store_id = 'gaja' OR store_name = (SELECT store_name FROM stores WHERE store_id = 'gaja');
DELETE FROM bays WHERE store_id = 'gaja';
DELETE FROM stores WHERE store_id = 'gaja';

COMMIT;

-- 확인
SELECT store_id FROM stores WHERE store_id = 'gaja';
```
