# Railway 배포 확인 가이드

**문제**: 코드에서 seed 데이터 생성 로직은 모두 제거했지만, Railway에서 여전히 "gaja" 매장이 생성됨

---

## 🔍 Railway Deploy Logs에서 확인할 항목

### 1. 배포 로그 메시지 확인

**이전 코드 (seed 데이터 생성)**: 
```
✅ DB 준비 완료
```

**현재 코드 (seed 제거)**: 
```
✅ DB 스키마 초기화 완료 (테이블/인덱스만 생성)
```

### 2. 각 서비스별 배포 커밋 SHA 확인

Railway 대시보드 → 각 서비스 → Deployments 탭:
- Super Admin: `e6b5470` 포함 여부
- User: `e6b5470` 포함 여부  
- Store Admin: `e6b5470` 포함 여부
- API: `e6b5470` 포함 여부

### 3. Git 브랜치 설정 확인

Railway 대시보드 → 각 서비스 → Settings → Source:
- Branch: `main` 설정 여부
- Auto Deploy: 활성화 여부

---

## 🔧 즉시 확인 방법

Railway Deploy Logs에서 다음을 검색:

### 검색 키워드
- `✅ DB 준비 완료` → **이전 코드 실행 중**
- `✅ DB 스키마 초기화 완료` → **최신 코드 실행 중**
- `기본 매장 생성` → **이전 코드 실행 중** (현재 코드에는 없음)

---

## 💡 해결 방법

1. **각 서비스 수동 재배포**
   - Railway 대시보드 → 각 서비스 → Deployments → "Redeploy"

2. **빌드 캐시 클리어 후 재배포**
   - Settings → Build & Deploy → "Clear Build Cache" → 재배포

3. **Git 커밋 SHA 확인**
   - Deployments 탭에서 최신 배포의 커밋 SHA가 `e6b5470`인지 확인
   - 이전 SHA라면 수동으로 최신 커밋 배포

---

## 📋 코드 레벨 검증 완료

✅ `services/super_admin/shared/database.py` - seed 제거  
✅ `services/user/shared/database.py` - seed 제거  
✅ `services/store_admin/shared/database.py` - seed 제거  
✅ `services/api/shared/database.py` - seed 제거  

---

## ⚠️ 반드시 확인해야 할 3가지 (CRITICAL)

### 1️⃣ DB에 이미 남아있는 gaja 데이터

**확인 쿼리** (Railway PostgreSQL):
```sql
SELECT store_id, store_name, created_at
FROM stores
WHERE store_id = 'gaja';
```

**결과**:
- `created_at`이 **최근 배포 시점 이전**이면 → 과거 seed 데이터
- **수동 삭제 필요**: `DELETE FROM stores WHERE store_id = 'gaja';`

**⚠️ Seed 제거 ≠ 기존 데이터 자동 삭제**

---

### 2️⃣ 환경 변수 확인 (매우 중요)

Railway 대시보드 → 각 서비스 → Settings → Variables:

**확인 항목**:
- `APP_ENV` (값: `production` 이어야 함)
- `ENV` (값: `production` 이어야 함)
- `RAILWAY_ENVIRONMENT` (값: `production` 이어야 함)

**❌ 하나라도 `dev`면 seed 코드가 실행될 수 있음**

---

### 3️⃣ PC 등록/라이선스 경로 암묵적 생성 확인

**확인 위치**:
- `register_store_pc()` 함수
- 라이선스 검증 로직
- 매장 조회 시 "없으면 생성" 코드

**검증 결과**: ✅ 현재 코드에서는 발견되지 않음

---

## 🧠 원인 후보 TOP 3

1. Railway 일부 서비스가 이전 커밋 실행 중
2. **DB에 기존 gaja 데이터 존재** ⭐ (가장 가능성 높음)
3. PC 등록 경로 암묵적 생성 (현재 코드에서는 없음)

---

**⚠️ 주의**

Seed 제거 후에도 기존 DB에 생성된 매장은 자동으로 삭제되지 않습니다.
Railway PostgreSQL에 gaja 데이터가 남아 있는 경우, 수동 삭제가 필요합니다.

**결론**: 코드는 정상입니다. Railway 배포 상태 및 **DB 내 기존 데이터**를 확인하세요.
