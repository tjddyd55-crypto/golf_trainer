# Railway 브랜치 오류 빠른 해결

## 문제
"Connected branch does not exist" 오류

## 원인
GitHub 저장소에 아직 코드가 푸시되지 않았습니다.

---

## 즉시 해결 방법

### 1단계: 모든 파일 커밋
PowerShell에서 실행:
```powershell
git add .
git commit -m "Initial commit: Golf Trainer 서비스 분리 완료"
```

### 2단계: GitHub 저장소 확인
- GitHub에서 `golftrainer` 저장소가 있는지 확인
- 없으면: https://github.com/new 에서 생성

### 3단계: 원격 저장소 연결
```powershell
# 원격 저장소가 없으면
git remote add origin https://github.com/[사용자명]/golftrainer.git

# 원격 저장소 확인
git remote -v
```

### 4단계: GitHub에 푸시
```powershell
git push -u origin main
```

### 5단계: Railway에서 재연결
1. Railway 대시보드에서 각 서비스 선택
2. **Settings** 탭 클릭
3. **Source** 섹션에서 **Disconnect** 클릭
4. 다시 **Connect GitHub** 클릭
5. 저장소: `golftrainer` 선택
6. 브랜치: `main` 선택
7. **Deploy** 클릭

---

## Railway에서 브랜치 연결 해제 (임시 방법)

각 서비스에서:
1. **Settings** → **Source**
2. **Disconnect** 버튼 클릭
3. 이렇게 하면 오류는 사라지지만 자동 배포는 안 됨
4. 수동으로 배포하거나 Railway CLI 사용

---

## 확인
- GitHub 저장소에 `main` 브랜치가 있는지 확인
- 코드가 푸시되었는지 확인
- Railway에서 브랜치를 `main`으로 설정
