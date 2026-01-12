-- ============================================================
-- 등록 코드 생성 SQL (Railway PostgreSQL에서 즉시 실행)
-- ============================================================

-- 1. 기존 ACTIVE 코드를 REVOKED로 변경
UPDATE pc_registration_codes 
SET status = 'REVOKED', 
    revoked_at = CURRENT_TIMESTAMP
WHERE status = 'ACTIVE';

-- 2. 새 등록 코드 생성 (GOLF-1234)
INSERT INTO pc_registration_codes (code, status, issued_by, notes)
VALUES ('GOLF-1234', 'ACTIVE', 'test_admin', '테스트용 등록 코드')
ON CONFLICT (code) DO UPDATE 
SET status = 'ACTIVE', 
    revoked_at = NULL,
    issued_by = EXCLUDED.issued_by,
    notes = EXCLUDED.notes
RETURNING code, status, created_at;

-- 3. 생성 확인
SELECT 
    code AS "등록 코드",
    status AS "상태",
    created_at AS "생성일시",
    issued_by AS "발급자"
FROM pc_registration_codes 
WHERE status = 'ACTIVE'
ORDER BY created_at DESC;
