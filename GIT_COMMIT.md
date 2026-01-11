# Git 커밋 및 GitHub 푸시 가이드

## 📝 Git 커밋 준비 완료

현재 프로젝트의 모든 파일이 Git에 추가되었습니다. 다음 단계를 진행하세요.

---

## 1️⃣ Git 사용자 정보 설정 (처음만)

```bash
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"
```

또는 이 저장소에만 설정:
```bash
git config user.email "your-email@example.com"
git config user.name "Your Name"
```

---

## 2️⃣ 커밋 실행

```bash
git commit -m "Initial commit: Golf Trainer project with Railway deployment setup"
```

---

## 3️⃣ GitHub 저장소 생성 및 연결

### GitHub 저장소 생성
1. GitHub (https://github.com) 접속
2. 우측 상단 "+" 버튼 클릭 → "New repository"
3. Repository name: `golf_trainer`
4. Visibility: Public 또는 Private 선택
5. "Create repository" 클릭

### 원격 저장소 연결
```bash
# YOUR_USERNAME을 본인의 GitHub 사용자명으로 변경
git remote add origin https://github.com/YOUR_USERNAME/golf_trainer.git
```

---

## 4️⃣ 코드 푸시

```bash
git push -u origin main
```

---

## 5️⃣ Railway 배포

코드가 GitHub에 푸시되면:
1. Railway (https://railway.app) 접속
2. "New Project" → "Deploy from GitHub repo"
3. `golf_trainer` 저장소 선택
4. 자동 배포 시작

---

## ✅ 완료!

배포가 완료되면 Railway에서 서비스 URL을 확인하고, 클라이언트(`main.py`)에서 해당 URL로 연결하세요.
