# 등록 코드 확인 및 생성 가이드

## 방법 1: Railway PostgreSQL에서 SQL 실행 (권장)

Railway 대시보드 → PostgreSQL 서비스 → Query 탭에서 아래 SQL 실행:

```sql
-- 1. 현재 ACTIVE 등록 코드 확인
SELECT code, status, created_at 
FROM pc_registration_codes 
WHERE status = 'ACTIVE'
ORDER BY created_at DESC;

-- 2. ACTIVE 코드가 없으면 생성
-- 기존 ACTIVE 코드를 REVOKED로 변경
UPDATE pc_registration_codes 
SET status = 'REVOKED', 
    revoked_at = CURRENT_TIMESTAMP
WHERE status = 'ACTIVE';

-- 새 테스트용 등록 코드 생성
INSERT INTO pc_registration_codes (code, status, issued_by, notes)
VALUES ('GOLF-1234', 'ACTIVE', 'test_admin', '테스트용 등록 코드')
ON CONFLICT (code) DO UPDATE 
SET status = 'ACTIVE', 
    revoked_at = NULL
RETURNING code, status, created_at;
```

## 방법 2: 슈퍼 관리자 API 사용

Railway super-admin 서비스가 배포되어 있다면:

```powershell
# PowerShell
$body = @{
    notes = "테스트용 등록 코드"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://golf-super-admin-production.up.railway.app/api/create_registration_code" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
```

## 빠른 생성 (단일 SQL)

Railway PostgreSQL Query 탭에서 실행:

```sql
-- 기존 ACTIVE 코드를 REVOKED로 변경하고 새 코드 생성
UPDATE pc_registration_codes 
SET status = 'REVOKED', revoked_at = CURRENT_TIMESTAMP
WHERE status = 'ACTIVE';

INSERT INTO pc_registration_codes (code, status, issued_by, notes)
VALUES ('GOLF-1234', 'ACTIVE', 'test_admin', '테스트용')
ON CONFLICT (code) DO UPDATE SET status = 'ACTIVE', revoked_at = NULL
RETURNING code, status, created_at;
```

생성된 코드: `GOLF-1234`

## 사용 방법

PC 등록 프로그램 실행 시:
- PC 등록 코드: `GOLF-1234` (생성한 코드)
- 매장명: 예) `가자24시`
- 룸 또는 타석: 예) `1번룸`
