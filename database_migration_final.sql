-- ============================================
-- 데이터베이스 마이그레이션 스크립트 (최종)
-- ============================================
-- 실행 순서:
-- 1. 사전 점검 쿼리 실행 (변환 실패할 값 확인)
-- 2. 타입 변환 쿼리 실행
-- 3. 인덱스 추가
-- ============================================

-- ============================================
-- 1-1. 사전 점검 (변환 실패할 값 확인)
-- ============================================

-- store_pcs 날짜 컬럼 점검
SELECT usage_end_date
FROM store_pcs
WHERE usage_end_date IS NOT NULL
  AND usage_end_date <> ''
  AND usage_end_date !~ '^\d{4}-\d{2}-\d{2}$'
LIMIT 50;

SELECT usage_start_date
FROM store_pcs
WHERE usage_start_date IS NOT NULL
  AND usage_start_date <> ''
  AND usage_start_date !~ '^\d{4}-\d{2}-\d{2}$'
LIMIT 50;

-- users.birth_date 점검
SELECT birth_date
FROM users
WHERE birth_date IS NOT NULL
  AND birth_date <> ''
  AND birth_date !~ '^\d{4}-\d{2}-\d{2}$'
LIMIT 50;

-- stores.subscription 날짜 점검
SELECT subscription_end_date
FROM stores
WHERE subscription_end_date IS NOT NULL
  AND subscription_end_date <> ''
  AND subscription_end_date !~ '^\d{4}-\d{2}-\d{2}$'
LIMIT 50;

-- ============================================
-- 1-2. 타입 변환 (안전한 변환)
-- ============================================

-- store_pcs: usage_end_date / usage_start_date TEXT -> DATE
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='store_pcs'
      AND column_name='usage_end_date' AND data_type='text'
  ) THEN
    ALTER TABLE store_pcs
      ALTER COLUMN usage_end_date TYPE DATE
      USING CASE
        WHEN usage_end_date IS NULL OR usage_end_date = '' THEN NULL
        WHEN usage_end_date ~ '^\d{4}-\d{2}-\d{2}$' THEN usage_end_date::DATE
        ELSE NULL
      END;
  END IF;

  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='store_pcs'
      AND column_name='usage_start_date' AND data_type='text'
  ) THEN
    ALTER TABLE store_pcs
      ALTER COLUMN usage_start_date TYPE DATE
      USING CASE
        WHEN usage_start_date IS NULL OR usage_start_date = '' THEN NULL
        WHEN usage_start_date ~ '^\d{4}-\d{2}-\d{2}$' THEN usage_start_date::DATE
        ELSE NULL
      END;
  END IF;
END $$;

-- users: birth_date TEXT -> DATE
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='users'
      AND column_name='birth_date' AND data_type='text'
  ) THEN
    ALTER TABLE users
      ALTER COLUMN birth_date TYPE DATE
      USING CASE
        WHEN birth_date IS NULL OR birth_date = '' THEN NULL
        WHEN birth_date ~ '^\d{4}-\d{2}-\d{2}$' THEN birth_date::DATE
        ELSE NULL
      END;
  END IF;
END $$;

-- stores: subscription_start_date / subscription_end_date TEXT -> DATE (권장)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='stores'
      AND column_name='subscription_end_date' AND data_type='text'
  ) THEN
    ALTER TABLE stores
      ALTER COLUMN subscription_end_date TYPE DATE
      USING CASE
        WHEN subscription_end_date IS NULL OR subscription_end_date = '' THEN NULL
        WHEN subscription_end_date ~ '^\d{4}-\d{2}-\d{2}$' THEN subscription_end_date::DATE
        ELSE NULL
      END;
  END IF;

  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='stores'
      AND column_name='subscription_start_date' AND data_type='text'
  ) THEN
    ALTER TABLE stores
      ALTER COLUMN subscription_start_date TYPE DATE
      USING CASE
        WHEN subscription_start_date IS NULL OR subscription_start_date = '' THEN NULL
        WHEN subscription_start_date ~ '^\d{4}-\d{2}-\d{2}$' THEN subscription_start_date::DATE
        ELSE NULL
      END;
  END IF;
END $$;

-- ============================================
-- 2. stores 테이블 컬럼 추가
-- ============================================

DO $$
BEGIN
  -- stores 테이블에 새 컬럼 추가
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='stores' AND column_name='contact'
  ) THEN
    ALTER TABLE stores ADD COLUMN contact TEXT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='stores' AND column_name='business_number'
  ) THEN
    ALTER TABLE stores ADD COLUMN business_number TEXT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='stores' AND column_name='owner_name'
  ) THEN
    ALTER TABLE stores ADD COLUMN owner_name TEXT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='stores' AND column_name='email'
  ) THEN
    ALTER TABLE stores ADD COLUMN email TEXT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='stores' AND column_name='address'
  ) THEN
    ALTER TABLE stores ADD COLUMN address TEXT;
  END IF;
END $$;

-- ============================================
-- 3. store_pcs 테이블 컬럼 추가
-- ============================================

DO $$
BEGIN
  -- store_pcs.store_id 확인 및 추가
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='store_pcs' AND column_name='store_id'
  ) THEN
    ALTER TABLE store_pcs ADD COLUMN store_id TEXT;
  END IF;

  -- store_pcs.bay_id 확인 및 추가
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='store_pcs' AND column_name='bay_id'
  ) THEN
    ALTER TABLE store_pcs ADD COLUMN bay_id TEXT;
  END IF;

  -- store_pcs.blocked_reason 추가
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='store_pcs' AND column_name='blocked_reason'
  ) THEN
    ALTER TABLE store_pcs ADD COLUMN blocked_reason TEXT;
  END IF;
END $$;

-- ============================================
-- 4. shots 테이블 컬럼 추가
-- ============================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='shots' AND column_name='pc_unique_id'
  ) THEN
    ALTER TABLE shots ADD COLUMN pc_unique_id TEXT;
  END IF;
END $$;

-- ============================================
-- 5. 인덱스 추가 (성능 최적화)
-- ============================================

CREATE INDEX IF NOT EXISTS idx_store_pcs_store_status_end
ON store_pcs (store_id, status, usage_end_date);

CREATE UNIQUE INDEX IF NOT EXISTS ux_stores_store_id
ON stores (store_id);

CREATE INDEX IF NOT EXISTS idx_shots_pc_unique_id
ON shots (pc_unique_id);

CREATE INDEX IF NOT EXISTS idx_shots_store_bay
ON shots (store_id, bay_id);
