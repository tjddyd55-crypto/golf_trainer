# Seed 데이터 제거 검증 보고서

**검증 일시**: 2026-01-19  
**목적**: 모든 서비스의 `init_db()`에서 seed 데이터 생성 로직 제거 확인

---

## ✅ 제거 완료 확인

### 1. Super Admin (`services/super_admin/shared/database.py`)
- **라인 326-328**: seed 데이터 생성 로직 제거됨 (주석만 존재)
- **상태**: ✅ 제거 완료

### 2. User (`services/user/shared/database.py`)
- **라인 289-291**: seed 데이터 생성 로직 제거됨 (주석만 존재)
- **상태**: ✅ 제거 완료

### 3. Store Admin (`services/store_admin/shared/database.py`)
- **라인 309-311**: seed 데이터 생성 로직 제거됨 (주석만 존재)
- **상태**: ✅ 제거 완료

### 4. API (`services/api/shared/database.py`)
- **라인 245-247**: seed 데이터 생성 로직 제거됨 (주석만 존재)
- **상태**: ✅ 제거 완료

---

## 🔍 남아있는 "gaja" 관련 코드 (정상)

### `create_store()` 함수 (의도된 동작)
- `super_admin/shared/database.py:631` - 매장 생성 함수 (수동 호출)
- `user/shared/database.py:1002` - 매장 생성 함수 (수동 호출)
- `store_admin/shared/database.py:714` - 매장 생성 함수 (수동 호출)
- `api/shared/database.py:542` - 매장 생성 함수 (수동 호출)

**이유**: 사용자가 매장을 생성할 때 호출하는 함수이므로 정상입니다.

### `seed_dev_data.py` (개발용 스크립트)
- `services/super_admin/seed_dev_data.py` - 개발 환경에서만 수동 실행

**이유**: 개발용 스크립트이므로 운영 환경에서 자동 실행되지 않습니다.

---

## ⚠️ 가능한 원인 (Railway 측 확인 필요)

1. **Railway가 이전 커밋을 배포하고 있을 수 있음**
   - 최신 커밋: `e6b5470` (store_admin/api 서비스 seed 제거)
   - Railway 대시보드에서 실제 배포된 커밋 SHA 확인 필요

2. **Railway 빌드 캐시 문제**
   - 이전 빌드 캐시를 사용 중일 수 있음
   - Railway에서 "Clear Build Cache" 후 재배포 필요

3. **여러 서비스 중 하나가 아직 업데이트 안 됨**
   - Super Admin, User, Store Admin, API 중 하나가 이전 버전을 실행 중일 수 있음
   - 각 서비스별 배포 상태 확인 필요

---

## 📋 Railway 대시보드에서 확인할 사항

1. **각 서비스의 Git 커밋 SHA**
   - Super Admin 서비스: 최신 커밋 `e6b5470` 포함 여부
   - User 서비스: 최신 커밋 `e6b5470` 포함 여부
   - Store Admin 서비스: 최신 커밋 `e6b5470` 포함 여부
   - API 서비스: 최신 커밋 `e6b5470` 포함 여부

2. **배포 로그 확인**
   - `✅ DB 스키마 초기화 완료 (테이블/인덱스만 생성)` 메시지 확인
   - `✅ DB 준비 완료` 메시지가 여전히 나타나면 이전 코드 실행 중

3. **재배포 필요 여부**
   - 각 서비스를 수동으로 재배포하거나
   - Railway에서 "Redeploy" 실행

---

## 🔧 임시 해결 방법

Railway에서 즉시 확인이 어려운 경우:

1. 로컬에서 모든 `init_db()` 함수가 seed 로직 없이 정상 작동하는지 확인
2. Railway Deploy Logs에서 `✅ DB 준비 완료` vs `✅ DB 스키마 초기화 완료` 메시지 비교
3. 필요시 각 서비스를 개별적으로 수동 재배포

---

## ⚠️ 반드시 추가 확인 필요 (CRITICAL)

### 1️⃣ DB에 이미 남아있는 gaja 데이터 확인

**중요**: Seed 제거 ≠ 기존 데이터 자동 삭제

**확인 쿼리**:
```sql
SELECT store_id, store_name, created_at
FROM stores
WHERE store_id = 'gaja';
```

**판단 기준**:
- `created_at`이 **최근 배포 시점 이전**이면 → 과거 seed 데이터가 그대로 남아 있음
- 이 경우 아무리 redeploy 해도 계속 보임

**권장 조치**:
```sql
-- gaja 매장 수동 삭제 (필요시)
DELETE FROM stores WHERE store_id = 'gaja';
DELETE FROM bays WHERE store_id = 'gaja';
```

**⚠️ 이걸 안 하면 "계속 생긴다"고 착각하기 딱 좋음**

---

### 2️⃣ 환경 변수 APP_ENV / ENV / RAILWAY_ENVIRONMENT 확인

Railway는 서비스별로 환경 변수가 다를 수 있음.

**각 서비스에서 반드시 확인**:
- `APP_ENV=production` 또는
- `ENV=production` 또는
- `RAILWAY_ENVIRONMENT=production`

**❌ 흔한 실수**:
- Super Admin만 `production`
- API는 `dev`
- User는 값 없음

**👉 단 하나라도 `dev`면 seed 코드가 살아있을 수 있음**

**Railway 확인 위치**:
- 각 서비스 → Settings → Variables
- `APP_ENV`, `ENV`, `RAILWAY_ENVIRONMENT` 값 확인

---

### 3️⃣ PC 등록/라이선스 검증 경로에서 암묵적 매장 생성 코드 확인

Seed가 아니라 "비즈니스 로직"으로 남아있을 수 있음.

**확인해야 할 패턴**:
```python
# ❌ 이런 코드 있으면 안 됨
if not store:
    store = create_default_store()
    # 또는
    store = create_store("gaja", "가자골프", "1111", 5)
```

**특히 확인할 위치**:
- PC 등록 API (`register_store_pc`)
- 라이선스 검증 API
- 최초 로그인 시 처리
- 매장 조회 시 "없으면 생성" 로직

**검증 결과**: ✅ 현재 코드에서는 발견되지 않음

---

## 🧠 결론 정리 (운영자 시점)

### 현재 상황의 진짜 원인 후보 TOP 3

1. **Railway 일부 서비스가 이전 커밋으로 실행 중**
2. **DB에 기존 gaja 데이터가 이미 존재** ⭐
3. **PC 등록/라이선스 경로에서 암묵적 생성** (현재 코드에서는 없음)

**👉 이 중 하나라도 맞으면 "배포하면 또 생김" 현상 발생**

---

**⚠️ 주의**

Seed 제거 후에도 기존 DB에 생성된 매장은 자동으로 삭제되지 않습니다.
Railway PostgreSQL에 gaja 데이터가 남아 있는 경우, 수동 삭제가 필요합니다.

또한 PC 등록/라이선스 검증 로직에서
매장 자동 생성 코드가 존재하지 않는지 반드시 확인해야 합니다.

---

**결론**: 코드 레벨에서는 모든 seed 데이터 생성 로직이 제거되었습니다. Railway 배포 상태 및 DB 내 기존 데이터를 확인해야 합니다.
