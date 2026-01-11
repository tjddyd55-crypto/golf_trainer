# Railway 서버 구성 가이드

## 개요
이 프로젝트는 4개의 독립적인 서비스로 구성되어 있습니다:
1. **API 서비스** - 샷 데이터 저장 및 PC 관리 API
2. **User 서비스** - 일반 사용자 웹 인터페이스
3. **Store Admin 서비스** - 매장 관리자 웹 인터페이스
4. **Super Admin 서비스** - 총책임자 웹 인터페이스

## 서버 구성 전략

### 옵션 1: 각 서비스를 별도 Railway 서비스로 배포 (권장)
각 서비스를 독립적으로 배포하여 확장성과 유지보수성을 높입니다.

### 옵션 2: 단일 서비스로 통합 배포
모든 서비스를 하나의 Railway 서비스에서 실행 (간단하지만 확장성 제한)

---

## 옵션 1: 별도 서비스 배포 (권장)

### 1. Railway 프로젝트 생성

1. Railway 대시보드에서 **New Project** 클릭
2. 프로젝트 이름: `golf-trainer` (또는 원하는 이름)
3. GitHub 저장소 연결: `golftrainer` 저장소 선택

### 2. 데이터베이스 서비스 추가

1. 프로젝트에서 **New** → **Database** → **PostgreSQL** 선택
2. 서비스 이름: `golf-trainer-db`
3. 자동으로 `DATABASE_URL` 환경 변수가 생성됨

### 3. API 서비스 배포

#### 서비스 생성
1. 프로젝트에서 **New** → **GitHub Repo** 선택
2. 같은 저장소(`golftrainer`) 선택
3. 서비스 이름: `golf-api`

#### 설정
- **Root Directory**: `services/api`
- **Build Command**: (비워둠 - Python은 자동 빌드)
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

#### 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<랜덤 문자열 생성>
PORT=5001
FLASK_DEBUG=False
```

#### Procfile (services/api/Procfile)
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### 4. User 서비스 배포

#### 서비스 생성
1. 프로젝트에서 **New** → **GitHub Repo** 선택
2. 같은 저장소(`golftrainer`) 선택
3. 서비스 이름: `golf-user`

#### 설정
- **Root Directory**: `services/user`
- **Build Command**: (비워둠)
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

#### 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<랜덤 문자열 생성>
PORT=5002
FLASK_DEBUG=False
SERVER_URL=${{golf-api.PUBLIC_URL}}
```

#### Procfile (services/user/Procfile)
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### 5. Store Admin 서비스 배포

#### 서비스 생성
1. 프로젝트에서 **New** → **GitHub Repo** 선택
2. 같은 저장소(`golftrainer`) 선택
3. 서비스 이름: `golf-store-admin`

#### 설정
- **Root Directory**: `services/store_admin`
- **Build Command**: (비워둠)
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

#### 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<랜덤 문자열 생성>
PORT=5003
FLASK_DEBUG=False
SERVER_URL=${{golf-api.PUBLIC_URL}}
```

#### Procfile (services/store_admin/Procfile)
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### 6. Super Admin 서비스 배포

#### 서비스 생성
1. 프로젝트에서 **New** → **GitHub Repo** 선택
2. 같은 저장소(`golftrainer`) 선택
3. 서비스 이름: `golf-super-admin`

#### 설정
- **Root Directory**: `services/super_admin`
- **Build Command**: (비워둠)
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

#### 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<랜덤 문자열 생성>
PORT=5004
FLASK_DEBUG=False
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=<강력한 비밀번호>
SERVER_URL=${{golf-api.PUBLIC_URL}}
```

#### Procfile (services/super_admin/Procfile)
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## 옵션 2: 단일 서비스 배포 (간단)

### 서비스 생성
1. Railway 대시보드에서 **New Project** → **GitHub Repo** 선택
2. 저장소: `golftrainer`
3. 서비스 이름: `golf-trainer`

### 설정
- **Root Directory**: `.` (루트 디렉토리)
- **Build Command**: (비워둠)
- **Start Command**: `python start_all_services.py` (아래 스크립트 필요)

### 환경 변수
```
DATABASE_URL=<PostgreSQL 연결 문자열>
FLASK_SECRET_KEY=<랜덤 문자열>
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=<강력한 비밀번호>
```

---

## 서비스 URL 구조

### 옵션 1 (별도 서비스) - 권장
- API: `https://golf-api.railway.app`
- User: `https://golf-user.railway.app`
- Store Admin: `https://golf-store-admin.railway.app`
- Super Admin: `https://golf-super-admin.railway.app`

### 옵션 2 (단일 서비스)
- 모든 서비스: `https://golf-trainer.railway.app`
- 라우팅: Nginx 또는 단일 Flask 앱에서 경로 분기

---

## 환경 변수 생성 가이드

### FLASK_SECRET_KEY 생성
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### DATABASE_URL
Railway PostgreSQL 서비스를 생성하면 자동으로 생성됩니다.
형식: `postgresql://user:password@host:port/database`

---

## 배포 체크리스트

### 공통
- [ ] PostgreSQL 데이터베이스 생성
- [ ] 각 서비스의 Root Directory 설정
- [ ] 환경 변수 설정
- [ ] Procfile 확인

### API 서비스
- [ ] `DATABASE_URL` 설정
- [ ] `FLASK_SECRET_KEY` 설정
- [ ] `PORT` 환경 변수 (선택사항, Railway가 자동 할당)

### User 서비스
- [ ] `DATABASE_URL` 설정
- [ ] `FLASK_SECRET_KEY` 설정
- [ ] `SERVER_URL` 설정 (API 서비스 URL)

### Store Admin 서비스
- [ ] `DATABASE_URL` 설정
- [ ] `FLASK_SECRET_KEY` 설정
- [ ] `SERVER_URL` 설정

### Super Admin 서비스
- [ ] `DATABASE_URL` 설정
- [ ] `FLASK_SECRET_KEY` 설정
- [ ] `SUPER_ADMIN_USERNAME` 설정
- [ ] `SUPER_ADMIN_PASSWORD` 설정 (강력한 비밀번호)
- [ ] `SERVER_URL` 설정

---

## 서비스 간 통신

### 내부 통신 (Railway 내부)
Railway 서비스 간에는 내부 네트워크를 통해 통신할 수 있습니다:
- `${{service-name.PUBLIC_URL}}` - 공개 URL
- `${{service-name.PRIVATE_URL}}` - 내부 URL (더 빠름)

### 권장 설정
- User/Store Admin/Super Admin → API: `${{golf-api.PRIVATE_URL}}` 사용 (내부 통신)
- 외부 클라이언트(main.py) → API: `${{golf-api.PUBLIC_URL}}` 사용

---

## 모니터링 및 로그

### Railway 대시보드
- 각 서비스의 로그 실시간 확인
- 메트릭 모니터링 (CPU, 메모리, 네트워크)
- 배포 히스토리

### 로그 확인
```bash
railway logs --service golf-api
railway logs --service golf-user
```

---

## 트러블슈팅

### 서비스가 시작되지 않음
1. Root Directory 확인
2. Procfile 경로 확인
3. 환경 변수 확인
4. 로그 확인

### 데이터베이스 연결 오류
1. `DATABASE_URL` 환경 변수 확인
2. PostgreSQL 서비스 상태 확인
3. 방화벽 설정 확인 (Railway는 자동 처리)

### 서비스 간 통신 오류
1. `SERVER_URL` 환경 변수 확인
2. 서비스 이름 확인 (`${{service-name.PUBLIC_URL}}`)

---

## 권장 사항

1. **별도 서비스 배포 (옵션 1) 권장**
   - 각 서비스 독립적 확장 가능
   - 장애 격리
   - 개별 배포 가능

2. **환경 변수 관리**
   - 민감한 정보는 Railway 환경 변수로 관리
   - 개발/프로덕션 환경 분리

3. **데이터베이스 백업**
   - Railway PostgreSQL 자동 백업 활용
   - 정기적인 수동 백업 권장

4. **도메인 연결**
   - 각 서비스에 커스텀 도메인 연결 가능
   - 예: `api.golftrainer.com`, `user.golftrainer.com`

---

## 다음 단계

1. Railway 프로젝트 생성
2. PostgreSQL 데이터베이스 추가
3. 각 서비스 순차적으로 배포
4. 환경 변수 설정
5. 테스트 및 검증
