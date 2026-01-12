-- ===== GOLF-TEST 코드 생성 SQL =====
-- Railway PostgreSQL Query 탭에서 실행하세요.

-- 기존 ACTIVE 코드를 REVOKED로 변경 (선택사항)
UPDATE pc_registration_codes 
SET status = 'REVOKED', 
    revoked_at = CURRENT_TIMESTAMP
WHERE status = 'ACTIVE';

-- GOLF-TEST 코드 생성 또는 활성화
INSERT INTO pc_registration_codes (
    code, 
    status, 
    issued_by, 
    notes,
    created_at
) VALUES (
    'GOLF-TEST',
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
WHERE code = 'GOLF-TEST';
