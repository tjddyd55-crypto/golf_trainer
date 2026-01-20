# Railway Start Command 수정 방법

## 문제
Railway UI에서 Start Command 변경이 안됨

## 해결 방법

### 방법 1: railway.json 파일 수정 (완료 ✅)

각 서비스의 `railway.json` 파일에서 `startCommand`를 수정했습니다:
- `services/api/railway.json`
- `services/user/railway.json`
- `services/store_admin/railway.json`
- `services/super_admin/railway.json`

모두 GitHub에 푸시되었습니다.

---

## Railway에서 해야 할 일

### 1. Root Directory 변경 (가장 중요!)

각 서비스의 **Settings** → **Deploy**에서:

**API 서비스 (golf-api)**:
- Root Directory: `.` (또는 비워둠)

**User 웹 서비스 (golf-user-web)**:
- Root Directory: `.` (또는 비워둠)

**Store Admin 서비스 (golf-store-admin)**:
- Root Directory: `.` (또는 비워둠)

**Super Admin 서비스 (golf-super-admin)**:
- Root Directory: `.` (또는 비워둠)

---

### 2. Start Command 확인

Railway가 `railway.json` 파일을 자동으로 읽어서 Start Command를 설정합니다.

만약 여전히 변경이 안되면:
1. **Settings** → **Deploy** → **Start Command** 필드 확인
2. 필드가 비어있거나 다른 값이면:
   - `cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT` 입력
   - (각 서비스에 맞게 `services/api` 부분 변경)

---

## 각 서비스별 Start Command

### API 서비스
```
cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT
```

### User 서비스
```
cd services/user && gunicorn app:app --bind 0.0.0.0:$PORT
```

### Store Admin 서비스
```
cd services/store_admin && gunicorn app:app --bind 0.0.0.0:$PORT
```

### Super Admin 서비스
```
cd services/super_admin && gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## 확인 사항

1. ✅ `railway.json` 파일 수정 완료 (GitHub 푸시됨)
2. ⏳ Railway에서 Root Directory를 `.`로 변경
3. ⏳ Railway가 자동으로 재배포 시작
4. ⏳ 로그에서 `shared` 모듈 오류 확인

---

## 만약 Start Command가 여전히 변경 안되면

Railway 대시보드에서:
1. 서비스 선택
2. **Settings** → **Deploy**
3. **Start Command** 필드에 직접 입력
4. **Save** 클릭

또는 Railway가 `railway.json`을 읽을 때까지 기다리기 (자동 재배포)
