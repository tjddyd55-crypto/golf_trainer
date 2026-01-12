-- 등록 코드 확인 및 생성 SQL 스크립트
-- Railway PostgreSQL에서 실행

-- 1. 현재 등록 코드 확인
SELECT 
    code,
    status,
    created_at,
    revoked_at,
    issued_by,
    notes
FROM pc_registration_codes
ORDER BY created_at DESC;

-- 2. ACTIVE 상태 등록 코드 확인
SELECT 
    code,
    status,
    created_at,
    issued_by
FROM pc_registration_codes
WHERE status = 'ACTIVE'
ORDER BY created_at DESC;

-- 3. ACTIVE 코드가 없으면 생성 (위 쿼리 결과가 없을 때만 실행)
-- 기존 ACTIVE 코드를 REVOKED로 변경
UPDATE pc_registration_codes 
SET status = 'REVOKED', 
    revoked_at = CURRENT_TIMESTAMP
WHERE status = 'ACTIVE';

-- 새 테스트용 등록 코드 생성 (GOLF-1234 형식)
INSERT INTO pc_registration_codes (code, status, issued_by, notes)
VALUES ('GOLF-1234', 'ACTIVE', 'test_admin', '테스트용 등록 코드')
ON CONFLICT (code) DO UPDATE 
SET status = 'ACTIVE', 
    revoked_at = NULL,
    issued_by = EXCLUDED.issued_by,
    notes = EXCLUDED.notes
RETURNING code, status, created_at;

-- 4. 생성된 코드 확인
SELECT code, status, created_at 
FROM pc_registration_codes 
WHERE status = 'ACTIVE';
