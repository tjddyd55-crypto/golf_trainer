# Railway 웹 서비스 추가 가이드

현재 PostgreSQL만 보이고 웹 서비스가 없는 경우, Flask 앱을 배포해야 합니다.

---

## 🚀 웹 서비스 배포 방법

### 방법 1: GitHub 저장소에서 배포 (권장)

#### 1단계: GitHub에 코드 푸시 확인
- [ ] GitHub에 `golf_trainer` 저장소가 있는지 확인
- [ ] 모든 코드가 푸시되었는지 확인

#### 2단계: Railway에서 웹 서비스 추가
1. Railway 대시보드에서 `golf_trainer` 프로젝트 선택
2. 우측 상단의 **"+ Create"** 버튼 클릭
3. **"GitHub Repo"** 선택
4. `golf_trainer` 저장소 선택
5. 자동으로 웹 서비스가 생성되고 배포 시작됨

---

### 방법 2: 수동으로 서비스 추가

1. Railway 대시보드에서 `golf_trainer` 프로젝트 선택
2. **"+ Create"** 버튼 클릭
3. **"Empty Service"** 선택
4. 서비스 이름 입력 (예: "web" 또는 "golf-trainer")
5. GitHub 저장소 연결:
   - Settings → Source → Connect GitHub
   - `golf_trainer` 저장소 선택
6. 배포 자동 시작

---

## ✅ 배포 확인

웹 서비스가 추가되면:
1. 대시보드에 **Postgres**와 **웹 서비스** 두 개가 보여야 합니다
2. 웹 서비스 카드에서 URL 확인 가능
3. 배포 상태가 "Deploying" 또는 "Active"로 표시됨

---

## 🔍 현재 상태 확인

### 확인 사항:
- [ ] GitHub에 코드가 푸시되어 있는가?
- [ ] Railway 프로젝트에 웹 서비스가 있는가?
- [ ] 배포가 진행 중이거나 완료되었는가?

### 웹 서비스가 보이지 않는 경우:
1. **"+ Create"** 버튼 클릭하여 웹 서비스 추가
2. GitHub 저장소 연결 확인
3. 배포 로그 확인 (Deployments 탭)

---

## 📝 배포 후 확인

웹 서비스가 배포되면:
1. 웹 서비스 카드에서 URL 확인
2. URL 클릭하여 접속 테스트
3. 로그인 페이지가 표시되는지 확인

---

## 🐛 문제 해결

### 배포 실패 시:
1. **Deployments** 탭에서 로그 확인
2. 오류 메시지 확인
3. `requirements.txt` 의존성 확인
4. `Procfile` 형식 확인

### GitHub 연결 실패 시:
1. Railway → Settings → Source 확인
2. GitHub 권한 확인
3. 저장소 이름 확인

---

## 💡 팁

- 웹 서비스와 PostgreSQL은 자동으로 연결됩니다
- `DATABASE_URL` 환경 변수는 자동으로 설정됩니다
- 배포는 보통 2-3분 소요됩니다
