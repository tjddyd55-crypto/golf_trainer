# 빠른 시작 가이드

## 🚀 배포까지 5단계

### 1️⃣ GitHub 저장소 생성 및 푸시
```bash
# 원격 저장소 연결
git remote add origin https://github.com/YOUR_USERNAME/golf_trainer.git

# 코드 푸시
git push -u origin main
```

### 2️⃣ Railway 프로젝트 생성
1. https://railway.app 접속
2. "New Project" → "Deploy from GitHub repo"
3. `golf_trainer` 저장소 선택
4. 자동 배포 시작 (2-3분)

### 3️⃣ PostgreSQL 추가
1. Railway 프로젝트에서 "New" → "Database" → "Add PostgreSQL"
2. `DATABASE_URL` 자동 설정됨 ✅

### 4️⃣ 서버 URL 확인
Railway 대시보드에서 서비스 URL 확인:
- 예: `https://golf-trainer-production.railway.app`

### 5️⃣ 클라이언트 설정
`start_client.bat` 파일 열어서 Railway URL 입력:
```batch
set SERVER_URL=https://your-railway-app.railway.app
```

또는 환경 변수로:
```powershell
$env:SERVER_URL="https://your-railway-app.railway.app"
python main.py
```

---

## ✅ 완료!

이제 골프 컴퓨터에서 `main.py`를 실행하면 Railway 서버로 데이터가 전송됩니다.

---

## 📚 상세 가이드
- 전체 배포 가이드: [GITHUB_DEPLOY.md](GITHUB_DEPLOY.md)
- 서버 세팅 가이드: [SERVER_SETUP.md](SERVER_SETUP.md)
- 배포 체크리스트: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
