# Railway 서비스 이름 확인

## 현재 보이는 서비스 이름들

이미지에서 확인된 이름:
- ✅ `golf-api`
- ✅ `golf-user-web`
- ✅ `golf-store-admin`
- ✅ `golf-super-admin`
- ⚠️ `Postgres` (PostgreSQL 서비스)

## 중요: PostgreSQL 서비스 이름 확인

환경 변수에서 사용하는 이름:
- 제가 알려준 것: `${{golf-trainer-db.DATABASE_URL}}`
- 실제 서비스 이름: `Postgres` (이미지 기준)

### 수정 필요

만약 PostgreSQL 서비스 이름이 `Postgres`라면:

**모든 서비스의 DATABASE_URL을 다음으로 변경:**
```
${{Postgres.DATABASE_URL}}
```

---

## 환경 변수 수정 버전

### 1. API 서비스 (golf-api)
```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
FLASK_SECRET_KEY = 344aa115c04a1e69f7c343e181e7e2c71738d0df9fc6a0b8081d263ad35e1263
FLASK_DEBUG = False
```

### 2. User 웹 서비스 (golf-user-web)
```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
FLASK_SECRET_KEY = a5b37e5c0224aba9e3e4c4fef0b47c5e766099d804b3b2dec90ecba9492d25c9
SERVER_URL = ${{golf-api.PUBLIC_URL}}
FLASK_DEBUG = False
```

### 3. Store Admin 서비스 (golf-store-admin)
```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
FLASK_SECRET_KEY = d78bf330f1331a3b6f3ee1ea496a7060b06f948a42d75b45e44a8b6be634b049
SERVER_URL = ${{golf-api.PUBLIC_URL}}
FLASK_DEBUG = False
```

### 4. Super Admin 서비스 (golf-super-admin)
```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
FLASK_SECRET_KEY = cc2e99bb5caffdfea5f33dfb8f3312f73093d80e07363b3edfe69083c6d061c0
SERVER_URL = ${{golf-api.PUBLIC_URL}}
SUPER_ADMIN_USERNAME = admin
SUPER_ADMIN_PASSWORD = <강력한 비밀번호>
FLASK_DEBUG = False
```

---

## 확인 방법

1. Railway 대시보드에서 PostgreSQL 서비스 클릭
2. Settings 탭 확인
3. 서비스 이름 확인
4. 그 이름을 `${{서비스이름.DATABASE_URL}}`에 사용
