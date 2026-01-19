-- ============================================================
-- STEP 1: DB 실체 확인 쿼리
-- Railway PostgreSQL Query Editor에서 실행하세요
-- ============================================================

-- 쿼리 1: 전체 store_pcs 확인
SELECT
  store_id,
  bay_id,
  bay_name,
  status,
  usage_end_date,
  pc_name
FROM store_pcs
WHERE store_id = 'testid2'  -- 또는 '가자스크린골프테스트2'
ORDER BY bay_id;

-- 쿼리 2: 활성 타석만 확인 (get_bays()와 동일 조건)
SELECT
  bay_id,
  bay_name,
  status,
  usage_end_date,
  pc_name
FROM store_pcs
WHERE store_id = 'testid2'  -- 또는 '가자스크린골프테스트2'
  AND status = 'active'
  AND bay_id IS NOT NULL
  AND bay_id != ''
  AND (usage_end_date IS NULL OR usage_end_date::date >= CURRENT_DATE)
ORDER BY bay_id;

-- ============================================================
-- 결과 해석:
-- 
-- ✅ 2줄 이상 나오면 → DB는 정상 → STEP 2로 (애플리케이션 로직 확인)
-- ❌ 1줄만 나오면 → DB 문제 확정 (관리자 승인 단계에서 1개만 active)
-- ⚠️ 0줄이면 → 활성 타석 없음 (관리자 화면에서 타석 승인 필요)
-- ============================================================
