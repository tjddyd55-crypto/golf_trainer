# 등록 코드 생성 가이드

## Railway PostgreSQL에서 실행

Railway 대시보드 → PostgreSQL 서비스 → Query 탭에서 아래 SQL 전체를 복사해서 실행하세요.

```sql
-- 기존 ACTIVE 코드를 REVOKED로 변경
UPDATE pc_registration_codes 
SET status = 'REVOKED', 
    revoked_at = CURRENT_TIMESTAMP
WHERE status = 'ACTIVE';

-- 새 등록 코드 생성 (GOLF-1234)
INSERT INTO pc_registration_codes (code, status, issued_by, notes)
VALUES ('GOLF-1234', 'ACTIVE', 'test_admin', '테스트용 등록 코드')
ON CONFLICT (code) DO UPDATE 
SET status = 'ACTIVE', 
    revoked_at = NULL,
    issued_by = EXCLUDED.issued_by,
    notes = EXCLUDED.notes
RETURNING code, status, created_at;

-- 생성 확인
SELECT 
    code AS "등록 코드",
    status AS "상태",
    created_at AS "생성일시"
FROM pc_registration_codes 
WHERE status = 'ACTIVE'
ORDER BY created_at DESC;
```

## 생성된 등록 코드

등록 코드: **GOLF-1234**

이 코드를 PC 등록 프로그램에서 사용하세요.

## 사용 방법

1. Railway PostgreSQL에서 위 SQL 실행
2. 생성 확인: 마지막 SELECT 결과에서 `GOLF-1234` 확인
3. PC 등록 프로그램 실행:
   ```bash
   dist\register_pc.exe
   ```
4. 입력:
   - PC 등록 코드: `GOLF-1234`
   - 매장명: 예) `가자24시`
   - 룸 또는 타석: 예) `1번룸`

## 주의사항

- 등록 코드는 대소문자를 구분합니다 (`GOLF-1234`)
- 정확히 입력해야 합니다
- 상태가 `ACTIVE`여야 사용 가능합니다
