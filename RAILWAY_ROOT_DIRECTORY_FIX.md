# Railway Root Directory 변경 방법

## 문제
Railway UI에서 Root Directory 변경이 안됨

## 해결 방법

### 방법 1: Settings에서 직접 변경

1. 서비스 선택 (예: golf-api)
2. **Settings** 탭
3. **Deploy** 섹션 찾기
4. **Root Directory** 필드 찾기
5. 값 입력: `.` (점 하나)
6. **Save** 버튼 클릭

### 방법 2: Settings에 Root Directory 필드가 없으면

Railway의 일부 버전에서는 Root Directory 설정이 다른 위치에 있을 수 있습니다:

1. **Settings** → **General** 섹션 확인
2. 또는 **Settings** → **Build** 섹션 확인
3. **Source** 섹션 확인

### 방법 3: Railway CLI 사용

터미널에서:
```bash
# Railway CLI 설치 (없으면)
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 연결
railway link

# 서비스 선택
railway service

# Root Directory 설정 (직접 설정 불가능할 수 있음)
```

### 방법 4: 서비스 재생성 (최후의 수단)

1. 기존 서비스 삭제
2. **New** → **GitHub Repo** 선택
3. 같은 저장소 선택
4. **서비스 생성 시 Root Directory를 `.`로 설정**

---

## 확인 사항

Railway에서 Root Directory 필드를 찾을 수 없는 경우:
- Railway 버전 문제일 수 있음
- 또는 프로젝트 타입에 따라 다를 수 있음

---

## 임시 해결책

Root Directory를 변경할 수 없다면, 각 서비스 디렉토리에 `shared` 폴더를 복사하는 방법을 사용해야 합니다.
