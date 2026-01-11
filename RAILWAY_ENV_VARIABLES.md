# Railway 환경 변수 설정 가이드

## 공통 설정 방법
1. Railway 대시보드 → 서비스 선택
2. **Variables** 탭 클릭
3. **New Variable** 클릭
4. 아래 변수들을 하나씩 추가

---

## 1. API 서비스 (golf-api)

### 필수 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<랜덤 문자열>
PORT=5001
FLASK_DEBUG=False
```

### 설정 방법
1. **DATABASE_URL**: 
   - 변수명: `DATABASE_URL`
   - 값: `${{golf-trainer-db.DATABASE_URL}}` (PostgreSQL 서비스 참조)
   - 또는 PostgreSQL 서비스의 Variables에서 `DATABASE_URL` 복사

2. **FLASK_SECRET_KEY**:
   - 변수명: `FLASK_SECRET_KEY`
   - 값: 랜덤 문자열 생성 (아래 참고)

3. **PORT** (선택사항):
   - Railway가 자동 할당하므로 생략 가능

4. **FLASK_DEBUG**:
   - 변수명: `FLASK_DEBUG`
   - 값: `False`

---

## 2. User 서비스 (golf-user)

### 필수 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<랜덤 문자열>
SERVER_URL=${{golf-api.PUBLIC_URL}}
FLASK_DEBUG=False
```

### 설정 방법
1. **DATABASE_URL**: `${{golf-trainer-db.DATABASE_URL}}`
2. **FLASK_SECRET_KEY**: API와 다른 키 사용 권장
3. **SERVER_URL**: `${{golf-api.PUBLIC_URL}}` (API 서비스 URL)
4. **FLASK_DEBUG**: `False`

---

## 3. Store Admin 서비스 (golf-store-admin)

### 필수 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<랜덤 문자열>
SERVER_URL=${{golf-api.PUBLIC_URL}}
FLASK_DEBUG=False
```

### 설정 방법
1. **DATABASE_URL**: `${{golf-trainer-db.DATABASE_URL}}`
2. **FLASK_SECRET_KEY**: 다른 키 사용 권장
3. **SERVER_URL**: `${{golf-api.PUBLIC_URL}}`
4. **FLASK_DEBUG**: `False`

---

## 4. Super Admin 서비스 (golf-super-admin)

### 필수 환경 변수
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<랜덤 문자열>
SERVER_URL=${{golf-api.PUBLIC_URL}}
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=<강력한 비밀번호>
FLASK_DEBUG=False
```

### 설정 방법
1. **DATABASE_URL**: `${{golf-trainer-db.DATABASE_URL}}`
2. **FLASK_SECRET_KEY**: 다른 키 사용 권장
3. **SERVER_URL**: `${{golf-api.PUBLIC_URL}}`
4. **SUPER_ADMIN_USERNAME**: `admin` (또는 원하는 사용자명)
5. **SUPER_ADMIN_PASSWORD**: 강력한 비밀번호 설정
6. **FLASK_DEBUG**: `False`

---

## FLASK_SECRET_KEY 생성 방법

### 방법 1: Python으로 생성
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 방법 2: 온라인 생성기 사용
- https://randomkeygen.com/

### 각 서비스별로 다른 키 사용 권장
- API: `<키1>`
- User: `<키2>`
- Store Admin: `<키3>`
- Super Admin: `<키4>`

---

## Railway에서 서비스 참조 방법

### DATABASE_URL
PostgreSQL 서비스 이름이 `golf-trainer-db`인 경우:
```
${{golf-trainer-db.DATABASE_URL}}
```

### SERVER_URL (API 서비스 URL)
API 서비스 이름이 `golf-api`인 경우:
```
${{golf-api.PUBLIC_URL}}
```

**참고**: 서비스 이름이 다르면 실제 서비스 이름으로 변경

---

## 빠른 설정 체크리스트

### API 서비스
- [ ] DATABASE_URL: `${{golf-trainer-db.DATABASE_URL}}`
- [ ] FLASK_SECRET_KEY: `<생성된 키>`
- [ ] FLASK_DEBUG: `False`

### User 서비스
- [ ] DATABASE_URL: `${{golf-trainer-db.DATABASE_URL}}`
- [ ] FLASK_SECRET_KEY: `<생성된 키>`
- [ ] SERVER_URL: `${{golf-api.PUBLIC_URL}}`
- [ ] FLASK_DEBUG: `False`

### Store Admin 서비스
- [ ] DATABASE_URL: `${{golf-trainer-db.DATABASE_URL}}`
- [ ] FLASK_SECRET_KEY: `<생성된 키>`
- [ ] SERVER_URL: `${{golf-api.PUBLIC_URL}}`
- [ ] FLASK_DEBUG: `False`

### Super Admin 서비스
- [ ] DATABASE_URL: `${{golf-trainer-db.DATABASE_URL}}`
- [ ] FLASK_SECRET_KEY: `<생성된 키>`
- [ ] SERVER_URL: `${{golf-api.PUBLIC_URL}}`
- [ ] SUPER_ADMIN_USERNAME: `admin`
- [ ] SUPER_ADMIN_PASSWORD: `<강력한 비밀번호>`
- [ ] FLASK_DEBUG: `False`

---

## 중요 사항

1. **서비스 이름 확인**: `${{service-name}}`에서 서비스 이름이 정확한지 확인
2. **DATABASE_URL**: PostgreSQL 서비스가 먼저 생성되어 있어야 함
3. **SERVER_URL**: API 서비스가 배포된 후 URL 확인
4. **FLASK_SECRET_KEY**: 각 서비스마다 다른 키 사용 권장
