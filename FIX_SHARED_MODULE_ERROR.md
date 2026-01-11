# shared 모듈 오류 해결

## 문제
`ModuleNotFoundError: No module named 'shared'`

## 원인
Root Directory가 `services/api`로 설정되어 있어서 루트의 `shared/` 폴더를 찾을 수 없음

## 해결 방법

### API 서비스 설정 변경

1. **Settings** → **Deploy** 섹션
2. **Root Directory** 변경:
   - 기존: `services/api`
   - 변경: `.` (또는 비워둠)
3. **Start Command** 변경:
   - 기존: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - 변경: `cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT`

---

## 각 서비스별 설정

### 1. API 서비스 (golf-api)
- **Root Directory**: `.` (루트)
- **Start Command**: `cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT`

### 2. User 서비스 (golf-user)
- **Root Directory**: `.` (루트)
- **Start Command**: `cd services/user && gunicorn app:app --bind 0.0.0.0:$PORT`

### 3. Store Admin 서비스 (golf-store-admin)
- **Root Directory**: `.` (루트)
- **Start Command**: `cd services/store_admin && gunicorn app:app --bind 0.0.0.0:$PORT`

### 4. Super Admin 서비스 (golf-super-admin)
- **Root Directory**: `.` (루트)
- **Start Command**: `cd services/super_admin && gunicorn app:app --bind 0.0.0.0:$PORT`

---

## 설정 후 확인
- `shared/` 모듈을 찾을 수 있음
- `static/` 폴더도 접근 가능
- 모든 서비스가 정상 작동
