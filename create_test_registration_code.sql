-- ===== 테스트용 등록 코드 생성 SQL =====
-- Railway PostgreSQL에서 직접 실행하세요.

-- 기존 ACTIVE 코드를 REVOKED로 변경
UPDATE pc_registration_codes 
SET status = 'REVOKED', 
    revoked_at = CURRENT_TIMESTAMP
WHERE status = 'ACTIVE';

-- 새 등록 코드 생성 (예: GOLF-1234)
INSERT INTO pc_registration_codes (
    code, 
    status, 
    issued_by, 
    notes,
    created_at
) VALUES (
    'GOLF-TEST',  -- 테스트용 코드 (원하는 코드로 변경 가능)
    'ACTIVE',
    'test_script',
    '테스트용 등록 코드',
    CURRENT_TIMESTAMP
)
ON CONFLICT (code) DO UPDATE SET
    status = 'ACTIVE',
    revoked_at = NULL,
    issued_by = 'test_script',
    notes = '테스트용 등록 코드',
    created_at = CURRENT_TIMESTAMP;

-- 생성된 코드 확인
SELECT code, status, issued_by, created_at 
FROM pc_registration_codes 
WHERE status = 'ACTIVE'
ORDER BY created_at DESC
LIMIT 1;
