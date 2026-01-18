# gaja 매장 데이터 삭제 가이드

Railway PostgreSQL에서 gaja 매장 데이터를 확인하고 삭제하는 방법입니다.

---

## 방법 1: Python 스크립트 사용 (권장)

### 1. Railway에서 DATABASE_URL 확인

1. Railway 대시보드 → PostgreSQL 서비스 → **Variables** 탭
2. `DATABASE_URL` 변수 값 복사

### 2. 로컬에서 스크립트 실행

```powershell
# PowerShell
$env:DATABASE_URL="postgresql://user:password@host:port/database"
python check_and_delete_gaja.py
```

또는:

```cmd
# CMD
set DATABASE_URL=postgresql://user:password@host:port/database
python check_and_delete_gaja.py
```

### 3. 스크립트가 자동으로:
- gaja 매장 데이터 확인
- 관련 타석/PC/샷 데이터 확인
- 삭제 전 확인 요청
- 안전하게 순서대로 삭제

---

## 방법 2: Railway Query Editor 사용

### 1. Railway 대시보드 접속

1. Railway 대시보드 → PostgreSQL 서비스
2. **Query** 탭 클릭

### 2. 확인 쿼리 실행

```sql
-- gaja 매장 확인
SELECT store_id, store_name, created_at 
FROM stores 
WHERE store_id = 'gaja';

-- 관련 데이터 확인
SELECT COUNT(*) as bays_count FROM bays WHERE store_id = 'gaja';
SELECT COUNT(*) as pcs_count FROM store_pcs WHERE store_id = 'gaja';
SELECT COUNT(*) as shots_count FROM shots WHERE store_id = 'gaja';
```

### 3. 삭제 쿼리 실행 (순서 중요!)

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

## ⚠️ 주의사항

1. **삭제 전 백업 권장**: 삭제 후 복구할 수 없습니다.
2. **삭제 순서 중요**: 외래 키 제약 때문에 위 순서를 따라야 합니다.
3. **확인 후 삭제**: 반드시 데이터를 확인한 후 삭제하세요.

---

## 결과 확인

삭제 후 확인 쿼리:

```sql
-- gaja 매장이 삭제되었는지 확인
SELECT store_id, store_name 
FROM stores 
WHERE store_id = 'gaja';
-- 결과: 0 rows
```

---

## 문제 해결

### DATABASE_URL 연결 오류

```
[ERROR] Database connection error: ...
```

**해결 방법**:
1. `DATABASE_URL` 값이 올바른지 확인
2. Railway PostgreSQL 서비스가 실행 중인지 확인
3. 네트워크 연결 확인

### 삭제 권한 오류

```
permission denied for table stores
```

**해결 방법**:
- Railway PostgreSQL 사용자는 일반적으로 모든 권한이 있습니다.
- 오류가 계속되면 Railway 지원팀에 문의하세요.
