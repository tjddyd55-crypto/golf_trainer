# Railway 서버 URL 확인 방법

Railway 대시보드에서 서비스 URL을 확인하는 방법입니다.

---

## 📍 방법 1: Railway 대시보드에서 확인

### 1단계: Railway 대시보드 접속
1. 브라우저에서 https://railway.app 접속
2. GitHub 계정으로 로그인

### 2단계: 프로젝트 선택
1. 대시보드에서 `golf_trainer` 프로젝트 클릭
2. (또는 배포한 프로젝트 이름 클릭)

### 3단계: 서비스 URL 확인
프로젝트 대시보드에서 다음 중 하나의 방법으로 URL 확인:

#### 방법 A: 서비스 카드에서 확인
- 프로젝트 대시보드의 메인 화면
- 배포된 서비스(웹 서비스) 카드에 URL 표시
- 예: `https://golf-trainer-production.railway.app`
- 또는 "View" 버튼 클릭

#### 방법 B: Settings에서 확인
1. 프로젝트 대시보드에서 **"Settings"** 탭 클릭
2. **"Domains"** 섹션 확인
3. Railway가 제공하는 기본 도메인 확인
   - 예: `https://golf-trainer-production.railway.app`

#### 방법 C: Deployments에서 확인
1. 프로젝트 대시보드에서 **"Deployments"** 탭 클릭
2. 최신 배포 클릭
3. 배포 상세 정보에서 URL 확인

#### 방법 D: 서비스 메뉴에서 확인
1. 프로젝트 대시보드에서 배포된 **웹 서비스** 클릭
2. 서비스 상세 페이지에서 **"Settings"** 탭 클릭
3. **"Domains"** 섹션에서 URL 확인

---

## 📍 방법 2: Railway CLI 사용 (선택사항)

Railway CLI가 설치되어 있다면:

```bash
railway status
```

또는:

```bash
railway domain
```

---

## 📍 방법 3: 배포 로그에서 확인

1. Railway 대시보드 → 프로젝트 선택
2. **"Deployments"** 탭 클릭
3. 최신 배포의 로그 확인
4. 로그에서 URL 정보 확인

---

## 🔍 URL 형식

Railway 서비스 URL은 일반적으로 다음과 같은 형식입니다:

```
https://[서비스이름]-[프로젝트이름].railway.app
```

예:
- `https://golf-trainer-production.railway.app`
- `https://web-production-xxxx.up.railway.app`
- `https://your-app-name.railway.app`

---

## ⚠️ 주의사항

1. **HTTPS 필수**: Railway는 자동으로 HTTPS를 제공합니다
2. **URL은 배포 후 생성**: 첫 배포가 완료되어야 URL이 생성됩니다
3. **커스텀 도메인**: 필요시 커스텀 도메인을 설정할 수 있습니다

---

## 🚀 빠른 확인 방법

가장 빠른 방법:
1. Railway 대시보드 접속
2. 프로젝트 선택
3. 메인 화면의 서비스 카드에서 URL 확인
4. 또는 "View" 버튼 클릭

---

## 📸 스크린샷 위치 (참고)

Railway 대시보드에서 URL을 확인할 수 있는 위치:
- ✅ 프로젝트 메인 대시보드 (서비스 카드)
- ✅ Settings → Domains
- ✅ 서비스 상세 페이지 → Settings → Domains
- ✅ Deployments → 배포 상세 정보

---

## 💡 팁

- URL을 복사하려면 URL 옆의 복사 버튼 클릭
- URL이 보이지 않으면 배포가 아직 완료되지 않았을 수 있습니다
- 배포 상태를 확인하려면 "Deployments" 탭 확인
