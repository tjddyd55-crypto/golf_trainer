# Railway 브랜치 오류 해결 방법

## 문제
"Connected branch does not exist" 오류가 발생하는 경우

## 원인
- GitHub 저장소에 아직 커밋이 없음
- 브랜치가 GitHub에 푸시되지 않음
- Railway가 잘못된 브랜치를 참조

---

## 해결 방법 1: GitHub에 코드 푸시 (권장)

### 1단계: 모든 변경사항 커밋
```bash
git add .
git commit -m "Initial commit: Golf Trainer 서비스 분리 완료"
```

### 2단계: GitHub 저장소 연결
```bash
git remote add origin https://github.com/[사용자명]/golftrainer.git
```

### 3단계: GitHub에 푸시
```bash
git push -u origin main
```

### 4단계: Railway에서 브랜치 재연결
1. Railway 대시보드에서 각 서비스 선택
2. **Settings** → **Source** 섹션
3. **Disconnect** 클릭
4. 다시 **Connect GitHub** 클릭
5. 저장소 선택: `golftrainer`
6. 브랜치 선택: `main`
7. **Deploy** 클릭

---

## 해결 방법 2: Railway에서 브랜치 연결 해제 (임시)

### 각 서비스에서 브랜치 연결 해제
1. Railway 대시보드에서 서비스 선택
2. **Settings** → **Source** 섹션
3. **Disconnect** 버튼 클릭
4. 수동 배포 사용 (Railway CLI 또는 GitHub Actions)

---

## 해결 방법 3: Railway CLI로 수동 배포

### Railway CLI 설치
```bash
npm i -g @railway/cli
railway login
```

### 프로젝트 연결
```bash
railway link
```

### 배포
```bash
# API 서비스 배포
cd services/api
railway up

# User 서비스 배포
cd ../user
railway up

# Store Admin 서비스 배포
cd ../store_admin
railway up

# Super Admin 서비스 배포
cd ../super_admin
railway up
```

---

## 빠른 해결 (지금 바로)

### 1. 현재 상태 확인
```bash
git status
```

### 2. 모든 파일 커밋
```bash
git add .
git commit -m "Initial commit: Golf Trainer 완성"
```

### 3. GitHub 저장소 확인
- GitHub에서 `golftrainer` 저장소가 있는지 확인
- 없으면 생성: https://github.com/new

### 4. 원격 저장소 연결 및 푸시
```bash
# 원격 저장소가 없으면 추가
git remote add origin https://github.com/[사용자명]/golftrainer.git

# 푸시
git push -u origin main
```

### 5. Railway에서 재연결
- 각 서비스의 Settings → Source에서
- Disconnect → Connect GitHub → main 브랜치 선택

---

## 확인 사항

### GitHub 저장소 확인
- [ ] 저장소가 생성되었는가?
- [ ] `main` 브랜치가 존재하는가?
- [ ] 코드가 푸시되었는가?

### Railway 설정 확인
- [ ] 각 서비스가 올바른 저장소를 참조하는가?
- [ ] 브랜치 이름이 `main`인가?
- [ ] Root Directory가 올바르게 설정되었는가?

---

## 문제가 계속되면

1. **Railway 대시보드에서 수동 배포**
   - Settings → Source → Disconnect
   - Settings → Deploy → Manual Deploy

2. **Railway 지원팀 문의**
   - Railway Discord 또는 이메일

3. **대안: Railway CLI 사용**
   - 브랜치 연결 없이 직접 배포
