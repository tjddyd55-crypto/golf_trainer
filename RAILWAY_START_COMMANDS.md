# Railway Start Command 설정

## 각 서비스별 Start Command

### 1. API 서비스 (golf-api)
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

### 2. User 서비스 (golf-user)
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

### 3. Store Admin 서비스 (golf-store-admin)
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

### 4. Super Admin 서비스 (golf-super-admin)
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## 설정 방법

1. Railway 대시보드 → 서비스 선택
2. **Settings** 탭
3. **Deploy** 섹션
4. **Start Command** 필드에 위 명령어 입력
5. **Save** 클릭

---

## 만약 "ModuleNotFoundError: No module named 'shared'" 오류가 발생하면

Root Directory가 `services/api`로 설정되어 있어서 `shared` 모듈을 찾지 못하는 경우:

### 해결 방법 1: Root Directory를 루트로 변경
- **Root Directory**: `.` (또는 비워둠)
- **Start Command**: `cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT`

### 해결 방법 2: PYTHONPATH 설정
- **Start Command**: `PYTHONPATH=/app gunicorn app:app --bind 0.0.0.0:$PORT`

### 해결 방법 3: 환경 변수 추가
- **Environment Variables**에 추가:
  ```
  PYTHONPATH=/app
  ```

---

## 우선순위

1. **먼저 시도**: `gunicorn app:app --bind 0.0.0.0:$PORT`
2. **오류 발생 시**: Root Directory를 `.`로 변경하고 Start Command를 `cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT`
