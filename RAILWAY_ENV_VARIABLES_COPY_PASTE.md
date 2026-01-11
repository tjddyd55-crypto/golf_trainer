# Railway 환경 변수 - 복사 붙여넣기용

## 1. API 서비스 (golf-api)

```
DATABASE_URL
${{golf-trainer-db.DATABASE_URL}}

FLASK_SECRET_KEY
<아래 키 복사>

FLASK_DEBUG
False
```

---

## 2. User 서비스 (golf-user)

```
DATABASE_URL
${{golf-trainer-db.DATABASE_URL}}

FLASK_SECRET_KEY
<아래 키 복사>

SERVER_URL
${{golf-api.PUBLIC_URL}}

FLASK_DEBUG
False
```

---

## 3. Store Admin 서비스 (golf-store-admin)

```
DATABASE_URL
${{golf-trainer-db.DATABASE_URL}}

FLASK_SECRET_KEY
<아래 키 복사>

SERVER_URL
${{golf-api.PUBLIC_URL}}

FLASK_DEBUG
False
```

---

## 4. Super Admin 서비스 (golf-super-admin)

```
DATABASE_URL
${{golf-trainer-db.DATABASE_URL}}

FLASK_SECRET_KEY
<아래 키 복사>

SERVER_URL
${{golf-api.PUBLIC_URL}}

SUPER_ADMIN_USERNAME
admin

SUPER_ADMIN_PASSWORD
<강력한 비밀번호 설정>

FLASK_DEBUG
False
```
