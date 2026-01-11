# Railway 배포 체크리스트

## 프로젝트 구조

### Railway 프로젝트 이름
- **프로젝트**: `golf-trainer`
- **데이터베이스**: `golf-trainer-db`
- **API 서비스**: `golf-api`
- **User 서비스**: `golf-user`
- **Store Admin 서비스**: `golf-store-admin`
- **Super Admin 서비스**: `golf-super-admin`

---

## 1단계: Railway 프로젝트 생성

### 프로젝트 생성
1. Railway 대시보드 접속
2. **New Project** 클릭
3. 프로젝트 이름: `golf-trainer`
4. GitHub 저장소 연결: `golftrainer` 선택

---

## 2단계: PostgreSQL 데이터베이스 추가

### 데이터베이스 생성
1. 프로젝트에서 **New** → **Database** → **PostgreSQL** 선택
2. 서비스 이름: `golf-trainer-db`
3. 자동 생성되는 환경 변수:
   - `DATABASE_URL` (다른 서비스에서 참조)

---

## 3단계: API 서비스 배포

### 서비스 생성
1. **New** → **GitHub Repo** 선택
2. 저장소: `golftrainer` (같은 저장소)
3. 서비스 이름: `golf-api`

### 설정
- **Root Directory**: `services/api`
- **Build Command**: (비워둠)
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<생성된 키>
PORT=5001
FLASK_DEBUG=False
```

### 확인 사항
- [ ] Root Directory: `services/api`
- [ ] Procfile 존재 확인
- [ ] 환경 변수 설정 완료
- [ ] 배포 성공 확인
- [ ] Health check: `https://golf-api.railway.app/api/health`

---

## 4단계: User 서비스 배포

### 서비스 생성
1. **New** → **GitHub Repo** 선택
2. 저장소: `golftrainer`
3. 서비스 이름: `golf-user`

### 설정
- **Root Directory**: `services/user`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<생성된 키>
PORT=5002
FLASK_DEBUG=False
SERVER_URL=${{golf-api.PUBLIC_URL}}
```

### 확인 사항
- [ ] Root Directory: `services/user`
- [ ] 환경 변수 설정 완료
- [ ] 배포 성공 확인
- [ ] 로그인 페이지 접속 확인

---

## 5단계: Store Admin 서비스 배포

### 서비스 생성
1. **New** → **GitHub Repo** 선택
2. 저장소: `golftrainer`
3. 서비스 이름: `golf-store-admin`

### 설정
- **Root Directory**: `services/store_admin`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<생성된 키>
PORT=5003
FLASK_DEBUG=False
SERVER_URL=${{golf-api.PUBLIC_URL}}
```

### 확인 사항
- [ ] Root Directory: `services/store_admin`
- [ ] 환경 변수 설정 완료
- [ ] 배포 성공 확인
- [ ] 매장 관리자 로그인 페이지 접속 확인

---

## 6단계: Super Admin 서비스 배포

### 서비스 생성
1. **New** → **GitHub Repo** 선택
2. 저장소: `golftrainer`
3. 서비스 이름: `golf-super-admin`

### 설정
- **Root Directory**: `services/super_admin`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<생성된 키>
PORT=5004
FLASK_DEBUG=False
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=<강력한 비밀번호>
SERVER_URL=${{golf-api.PUBLIC_URL}}
```

### 확인 사항
- [ ] Root Directory: `services/super_admin`
- [ ] 환경 변수 설정 완료
- [ ] 배포 성공 확인
- [ ] 총책임자 로그인 페이지 접속 확인
- [ ] 로그인 테스트

---

## 7단계: 환경 변수 생성

### FLASK_SECRET_KEY 생성
로컬에서 실행:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

각 서비스에 다른 키 사용 권장:
- `golf-api`: `<키1>`
- `golf-user`: `<키2>`
- `golf-store-admin`: `<키3>`
- `golf-super-admin`: `<키4>`

---

## 8단계: 서비스 URL 확인

배포 완료 후 각 서비스의 공개 URL 확인:

- API: `https://golf-api.up.railway.app`
- User: `https://golf-user.up.railway.app`
- Store Admin: `https://golf-store-admin.up.railway.app`
- Super Admin: `https://golf-super-admin.up.railway.app`

---

## 9단계: 클라이언트 설정

### main.py 환경 변수
매장 PC에서 `shot_collector.exe` 실행 시:
```bash
set SERVER_URL=https://golf-api.up.railway.app
```

또는 `start_client.bat` 수정:
```batch
set SERVER_URL=https://golf-api.up.railway.app
python main.py
```

### register_pc.py
PC 등록 시 서버 URL 입력:
```
서버 URL: https://golf-user.up.railway.app
```

---

## 10단계: 테스트

### API 서비스 테스트
```bash
curl https://golf-api.up.railway.app/api/health
```

### User 서비스 테스트
1. 브라우저에서 `https://golf-user.up.railway.app` 접속
2. 회원가입 테스트
3. 로그인 테스트

### Store Admin 테스트
1. `https://golf-store-admin.up.railway.app` 접속
2. 매장 회원가입 테스트
3. 로그인 테스트

### Super Admin 테스트
1. `https://golf-super-admin.up.railway.app` 접속
2. 로그인 테스트 (설정한 계정)
3. PC 관리 페이지 확인

---

## 문제 해결

### 서비스가 시작되지 않음
1. **Root Directory 확인**: 각 서비스의 올바른 디렉토리 설정
2. **Procfile 확인**: `services/[service-name]/Procfile` 존재 확인
3. **로그 확인**: Railway 대시보드에서 로그 확인
4. **환경 변수 확인**: 필수 환경 변수 모두 설정되었는지 확인

### 데이터베이스 연결 오류
1. `DATABASE_URL` 환경 변수 확인
2. PostgreSQL 서비스 상태 확인
3. 연결 문자열 형식 확인

### 서비스 간 통신 오류
1. `SERVER_URL` 환경 변수 확인
2. API 서비스 URL이 올바른지 확인
3. 서비스 이름 확인 (`${{service-name.PUBLIC_URL}}`)

---

## 최종 확인

- [ ] 모든 서비스 배포 완료
- [ ] 데이터베이스 연결 확인
- [ ] 각 서비스 로그인 테스트
- [ ] PC 등록 테스트
- [ ] 샷 데이터 저장 테스트
- [ ] 슈퍼 관리자 승인 테스트

---

## 참고 문서

- [Railway 공식 문서](https://docs.railway.app/)
- [RAILWAY_SERVER_SETUP.md](./RAILWAY_SERVER_SETUP.md) - 상세 설정 가이드
- [DEPLOYMENT_MANUAL.md](./DEPLOYMENT_MANUAL.md) - 매장 설치 매뉴얼
