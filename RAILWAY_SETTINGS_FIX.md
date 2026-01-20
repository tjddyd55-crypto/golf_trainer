# Railway 설정 변경 가이드 (필수)

## 현재 문제
- `ModuleNotFoundError: No module named 'shared'`
- 서비스들이 계속 Crashed/Build failed 상태

## 해결 방법

### ⚠️ 중요: 모든 서비스에서 다음 설정을 변경해야 합니다

---

## 1. API 서비스 (golf-api) - 가장 먼저

### Settings → Deploy 섹션:

1. **Root Directory**:
   - 기존: `services/api` ❌
   - 변경: `.` (점 하나) 또는 **비워둠** ✅

2. **Start Command**:
   - 기존: `gunicorn app:app --bind 0.0.0.0:$PORT` ❌
   - 변경: `cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT` ✅

3. **Variables** (이미 설정했다면 확인):
   ```
   DATABASE_URL = ${{Postgres.DATABASE_URL}}
   FLASK_SECRET_KEY = 344aa115c04a1e69f7c343e181e7e2c71738d0df9fc6a0b8081d263ad35e1263
   FLASK_DEBUG = False
   ```

---

## 2. User 웹 서비스 (golf-user-web)

### Settings → Deploy 섹션:

1. **Root Directory**: `.` (또는 비워둠)
2. **Start Command**: `cd services/user && gunicorn app:app --bind 0.0.0.0:$PORT`

### Variables:
```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
FLASK_SECRET_KEY = a5b37e5c0224aba9e3e4c4fef0b47c5e766099d804b3b2dec90ecba9492d25c9
SERVER_URL = ${{golf-api.PUBLIC_URL}}
FLASK_DEBUG = False
```

---

## 3. Store Admin 서비스 (golf-store-admin)

### Settings → Deploy 섹션:

1. **Root Directory**: `.` (또는 비워둠)
2. **Start Command**: `cd services/store_admin && gunicorn app:app --bind 0.0.0.0:$PORT`

### Variables:
```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
FLASK_SECRET_KEY = d78bf330f1331a3b6f3ee1ea496a7060b06f948a42d75b45e44a8b6be634b049
SERVER_URL = ${{golf-api.PUBLIC_URL}}
FLASK_DEBUG = False
```

---

## 4. Super Admin 서비스 (golf-super-admin)

### Settings → Deploy 섹션:

1. **Root Directory**: `.` (또는 비워둠)
2. **Start Command**: `cd services/super_admin && gunicorn app:app --bind 0.0.0.0:$PORT`

### Variables:
```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
FLASK_SECRET_KEY = cc2e99bb5caffdfea5f33dfb8f3312f73093d80e07363b3edfe69083c6d061c0
SERVER_URL = ${{golf-api.PUBLIC_URL}}
SUPER_ADMIN_USERNAME = admin
SUPER_ADMIN_PASSWORD = <강력한 비밀번호>
FLASK_DEBUG = False
```

---

## 설정 후 확인

1. 각 서비스의 **Settings** → **Deploy**에서:
   - Root Directory가 `.`인지 확인
   - Start Command가 올바른지 확인

2. **Deployments** 탭에서:
   - 새로운 배포가 시작되는지 확인
   - 로그에서 오류가 사라졌는지 확인

---

## 왜 이렇게 해야 하나요?

- Root Directory가 `services/api`로 설정되면 Railway는 그 디렉토리만 빌드합니다
- `shared/` 폴더는 루트에 있으므로 찾을 수 없습니다
- Root Directory를 `.`로 설정하면 전체 프로젝트가 빌드되고 `shared/`를 찾을 수 있습니다
- Start Command에서 `cd services/api`로 이동한 후 실행합니다

---

## 순서

1. ✅ 코드 수정 완료 (GitHub 푸시됨)
2. ⏳ Railway에서 Root Directory 변경 (`.`)
3. ⏳ Start Command 변경 (`cd services/api && ...`)
4. ⏳ 배포 확인

**지금 Railway에서 API 서비스 설정을 변경해주세요!**
