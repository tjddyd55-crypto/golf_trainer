# Git 설정 및 GitHub 푸시 가이드

## 현재 상태
✅ 모든 파일이 스테이징됨
❌ Git 사용자 정보 미설정
❌ 원격 저장소 미연결
❌ 커밋 없음

---

## 해결 단계

### 1단계: Git 사용자 정보 설정
PowerShell에서 실행 (실제 정보로 변경):

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

또는 이 저장소에만 설정:
```powershell
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 2단계: 커밋
```powershell
git commit -m "Initial commit: Golf Trainer 서비스 분리 완료"
```

### 3단계: GitHub 저장소 확인
- GitHub에서 `golftrainer` 저장소가 있는지 확인
- 없으면 생성: https://github.com/new
- 저장소 이름: `golftrainer`

### 4단계: 원격 저장소 연결
```powershell
# 실제 GitHub 사용자명으로 변경
git remote add origin https://github.com/[사용자명]/golftrainer.git

# 확인
git remote -v
```

### 5단계: GitHub에 푸시
```powershell
git push -u origin main
```

---

## 확인 명령어

### Git 설정 확인
```powershell
git config --list
```

### 원격 저장소 확인
```powershell
git remote -v
```

### 커밋 확인
```powershell
git log --oneline
```

---

## Railway 브랜치 오류 해결

GitHub에 푸시 완료 후:
1. Railway 대시보드에서 각 서비스 선택
2. **Settings** → **Source**
3. **Disconnect** 클릭
4. **Connect GitHub** 클릭
5. 저장소: `golftrainer` 선택
6. 브랜치: `main` 선택
7. **Deploy** 클릭

---

## 빠른 실행 스크립트

PowerShell에서 한 번에 실행:

```powershell
# 1. Git 설정 (실제 정보로 변경 필요)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 2. 커밋
git commit -m "Initial commit: Golf Trainer 서비스 분리 완료"

# 3. 원격 저장소 연결 (실제 URL로 변경 필요)
git remote add origin https://github.com/[사용자명]/golftrainer.git

# 4. 푸시
git push -u origin main
```
