# Railway 배포 구조 가이드

## 🏗️ 서비스 분리 구조

### 3개의 독립 서비스 + 1개의 API 서비스

```
Railway 프로젝트 구조:

1. Super Admin 서비스
   - URL: https://super-admin.railway.app
   - 포트: 5002
   - 역할: 총책임자 (매장 관리, 결제, 사용기간)

2. Store Admin 서비스
   - URL: https://store-admin.railway.app
   - 포트: 5001
   - 역할: 매장 관리자 (유저 관리, 타석 관리)

3. User 서비스
   - URL: https://user.railway.app
   - 포트: 5000
   - 역할: 유저 (샷 기록 조회)

4. API 서비스 (선택사항)
   - URL: https://api.railway.app
   - 포트: 5003
   - 역할: 공통 API (main.py에서 사용)
```

## 📝 Railway 배포 설정

### 각 서비스별 Procfile

#### Super Admin
```
web: cd services/super_admin && gunicorn app:app --bind 0.0.0.0:$PORT
```

#### Store Admin
```
web: cd services/store_admin && gunicorn app:app --bind 0.0.0.0:$PORT
```

#### User
```
web: cd services/user && gunicorn app:app --bind 0.0.0.0:$PORT
```

#### API
```
web: cd services/api && gunicorn app:app --bind 0.0.0.0:$PORT
```

## 🔧 main.py 서버 URL 설정

main.py에서 각 서비스의 URL을 설정:

```python
# API 서비스 URL (샷 저장용)
API_SERVER_URL = os.environ.get("API_SERVER_URL", "https://api.railway.app")
SERVER_URL = f"{API_SERVER_URL}/api/save_shot"
ACTIVE_USER_API = f"{API_SERVER_URL}/api/active_user"
```

또는 User 서비스에 API 포함:

```python
# User 서비스에 API 포함 시
USER_SERVER_URL = os.environ.get("USER_SERVER_URL", "https://user.railway.app")
SERVER_URL = f"{USER_SERVER_URL}/api/save_shot"
```

## 🎯 권장 구성

### 옵션 1: User 서비스에 API 포함 (간단)
- User 서비스에 `/api/*` 엔드포인트 포함
- main.py는 User 서비스 URL 사용
- 서비스 3개만 필요

### 옵션 2: 별도 API 서비스 (확장성)
- API 서비스 분리
- main.py는 API 서비스 URL 사용
- 서비스 4개 필요

## 📋 배포 체크리스트

- [ ] Super Admin 서비스 배포
- [ ] Store Admin 서비스 배포
- [ ] User 서비스 배포
- [ ] API 서비스 배포 (선택사항)
- [ ] PostgreSQL 서비스 추가 (각 프로젝트 또는 공유)
- [ ] 환경 변수 설정
- [ ] main.py 서버 URL 업데이트
