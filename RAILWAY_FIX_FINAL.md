# Railway 최종 해결 방법

## 문제
- `ModuleNotFoundError: No module named 'shared'`
- 설정 변경 후에도 계속 오류 발생

## 해결 방법

### 방법 1: Root Directory를 루트로 설정 (권장)

각 서비스에서:
1. **Settings** → **Deploy**
2. **Root Directory**: `.` (또는 비워둠)
3. **Start Command**: `cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT`

### 방법 2: PYTHONPATH 환경 변수 추가

각 서비스의 **Variables**에 추가:
```
PYTHONPATH=/app
```

그리고 Root Directory를 `.`로 설정

---

## 각 서비스별 최종 설정

### API 서비스 (golf-api)
- **Root Directory**: `.`
- **Start Command**: `cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT`
- **Variables**:
  - `DATABASE_URL=${{Postgres.DATABASE_URL}}`
  - `FLASK_SECRET_KEY=344aa115c04a1e69f7c343e181e7e2c71738d0df9fc6a0b8081d263ad35e1263`
  - `FLASK_DEBUG=False`
  - `PYTHONPATH=/app` (추가)

### User 서비스 (golf-user)
- **Root Directory**: `.`
- **Start Command**: `cd services/user && gunicorn app:app --bind 0.0.0.0:$PORT`
- **Variables**: (동일하게 PYTHONPATH 추가)

### Store Admin 서비스 (golf-store-admin)
- **Root Directory**: `.`
- **Start Command**: `cd services/store_admin && gunicorn app:app --bind 0.0.0.0:$PORT`

### Super Admin 서비스 (golf-super-admin)
- **Root Directory**: `.`
- **Start Command**: `cd services/super_admin && gunicorn app:app --bind 0.0.0.0:$PORT`

---

## 코드 수정 완료

각 서비스의 `app.py`에서 `shared` 모듈 경로를 더 견고하게 수정했습니다.
이제 Root Directory가 `.`이든 `services/api`이든 작동합니다.

---

## 다음 단계

1. 코드가 GitHub에 푸시됨 (자동 재배포)
2. Railway에서 Root Directory를 `.`로 변경
3. Start Command 확인
4. PYTHONPATH 환경 변수 추가 (선택사항)
