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

**결론**: 코드는 정상입니다. Railway 배포 상태를 확인하세요.
