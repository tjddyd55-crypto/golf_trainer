# 데이터베이스 마이그레이션 실행 가이드

## 방법 1: Railway 대시보드에서 직접 실행 (권장)

1. Railway 대시보드 접속
2. PostgreSQL 서비스 선택
3. **Query** 탭 클릭
4. `database_migration_final.sql` 파일 내용을 복사하여 붙여넣기
5. **Run Query** 버튼 클릭

## 방법 2: Python 스크립트로 실행

### 준비사항
- Railway PostgreSQL의 **Public Network URL** 필요
  - Railway 대시보드 > PostgreSQL 서비스 > **Connect** 탭
  - **Public Network** 섹션의 URL 복사

### 실행 방법

#### 옵션 A: 환경 변수 사용
```bash
# Windows PowerShell
$env:DATABASE_URL="postgresql://postgres:password@host.railway.app:port/railway"
python run_migration_simple.py

# Windows CMD
set DATABASE_URL=postgresql://postgres:password@host.railway.app:port/railway
python run_migration_simple.py
```

#### 옵션 B: 직접 입력
```bash
python run_migration_simple.py
# 실행 후 DATABASE_URL 입력 프롬프트에 붙여넣기
```

## 마이그레이션 내용

1. **날짜 타입 변경**
   - `store_pcs.usage_start_date` → DATE
   - `store_pcs.usage_end_date` → DATE
   - `users.birth_date` → DATE
   - `stores.subscription_start_date` → DATE
   - `stores.subscription_end_date` → DATE

2. **컬럼 추가**
   - `stores`: contact, business_number, owner_name, email, address
   - `store_pcs`: store_id, bay_id, blocked_reason
   - `shots`: pc_unique_id

3. **인덱스 추가**
   - `idx_store_pcs_store_status_end`
   - `ux_stores_store_id` (UNIQUE)
   - `idx_shots_pc_unique_id`
   - `idx_shots_store_bay`

## 주의사항

- 마이그레이션은 **안전하게** 설계되었습니다
- 이미 존재하는 컬럼/인덱스는 자동으로 건너뜁니다
- 날짜 형식이 올바르지 않은 값은 NULL로 변환됩니다
- **백업 권장**: 마이그레이션 전 데이터 백업을 권장합니다

## 문제 해결

### 연결 오류
- Railway PostgreSQL 서비스가 실행 중인지 확인
- Public Network URL을 사용하고 있는지 확인
- 방화벽 설정 확인

### 마이그레이션 오류
- 이미 실행된 마이그레이션은 건너뛰어집니다
- 치명적 오류가 발생하면 Railway 로그 확인
