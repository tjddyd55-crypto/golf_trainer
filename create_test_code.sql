-- 테스트용 등록 코드 생성 SQL
-- Railway PostgreSQL 데이터베이스에서 실행

-- 1. 기존 ACTIVE 코드를 REVOKED로 변경
UPDATE pc_registration_codes 
SET status = 'REVOKED', 
    revoked_at = CURRENT_TIMESTAMP
WHERE status = 'ACTIVE';

-- 2. 새 테스트용 등록 코드 생성
INSERT INTO pc_registration_codes (code, status, issued_by, notes)
VALUES ('GOLF-TEST', 'ACTIVE', 'test_admin', '테스트용 등록 코드')
RETURNING code, status, created_at;

-- 3. 생성된 코드 확인
SELECT code, status, created_at, notes 
FROM pc_registration_codes 
WHERE status = 'ACTIVE'
ORDER BY created_at DESC;
