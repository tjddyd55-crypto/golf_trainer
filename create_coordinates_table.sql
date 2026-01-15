-- 좌표 파일 테이블 생성
CREATE TABLE IF NOT EXISTS coordinates (
  id SERIAL PRIMARY KEY,
  brand VARCHAR(50) NOT NULL,
  resolution VARCHAR(20) NOT NULL,
  version INTEGER NOT NULL,
  filename VARCHAR(100) NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (brand, resolution, version)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_coordinates_brand ON coordinates(brand);
CREATE INDEX IF NOT EXISTS idx_coordinates_brand_filename ON coordinates(brand, filename);
