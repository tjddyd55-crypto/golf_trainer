# 서비스 분리 구조 가이드

## 📁 디렉토리 구조

```
golf_trainer/
├── services/
│   ├── super_admin/          # 총책임자 서비스
│   │   ├── app.py
│   │   ├── utils.py
│   │   └── templates/
│   │       ├── super_admin_login.html
│   │       ├── super_admin_dashboard.html
│   │       ├── manage_stores.html
│   │       ├── manage_payments.html
│   │       └── manage_subscriptions.html
│   ├── store_admin/          # 매장 관리자 서비스
│   │   ├── app.py
│   │   ├── utils.py
│   │   └── templates/
│   │       ├── store_admin_login.html
│   │       ├── store_admin_signup.html
│   │       ├── store_admin_dashboard.html
│   │       └── bay_shots.html
│   ├── user/                 # 유저 서비스
│   │   ├── app.py
│   │   ├── utils.py
│   │   └── templates/
│   │       ├── user_login.html
│   │       ├── user_signup.html
│   │       ├── user_main.html
│   │       └── shots_all.html
│   └── api/                  # 공통 API 서비스 (선택사항)
│       └── app.py
├── shared/                   # 공유 모듈
│   ├── __init__.py
│   ├── database.py
│   └── auth.py
├── static/                   # 정적 파일
│   ├── css/
│   │   ├── user.css
│   │   ├── store_admin.css
│   │   └── super_admin.css
│   └── js/
├── config/                   # 설정 파일
│   ├── criteria.json
│   └── feedback_messages.json
└── main.py                   # 클라이언트 (골프 PC)
```

## 🚀 Railway 배포 방법

### 각 서비스를 별도 프로젝트로 배포

#### 1. Super Admin 서비스
- Railway 프로젝트: `golf-trainer-super-admin`
- 루트 디렉토리: `services/super_admin`
- Procfile:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

#### 2. Store Admin 서비스
- Railway 프로젝트: `golf-trainer-store-admin`
- 루트 디렉토리: `services/store_admin`
- Procfile:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

#### 3. User 서비스 (API 포함)
- Railway 프로젝트: `golf-trainer-user`
- 루트 디렉토리: `services/user`
- Procfile:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### PostgreSQL 설정
각 서비스는 동일한 PostgreSQL 데이터베이스를 사용:
- Railway에서 PostgreSQL 서비스 생성
- 각 서비스의 환경 변수에 `DATABASE_URL` 설정

## 🔑 타석 코드 기능

### 코드 형식
- 4자리: 영문 1자 + 숫자 3자
- 예: `A001`, `B123`, `G045`
- 매장 ID의 첫 글자 + 타석 번호

### 사용 흐름
1. 매장 등록 시 타석 코드 자동 생성
2. 타석 앞에 코드 표시 (QR 코드 또는 텍스트)
3. 유저가 앱에서 코드 입력
4. 자동으로 매장-타석 매칭
5. 세션 연결

### 코드 확인 API
```
POST /api/check_bay_code
{
    "bay_code": "A001"
}
```

## 🎨 CSS 구조

### CSS 파일 분리
- `static/css/user.css` - 유저 서비스
- `static/css/store_admin.css` - 매장 관리자
- `static/css/super_admin.css` - 총책임자

### CSS 변수 사용
각 CSS 파일에서 `:root`에 색상 변수 정의:
```css
:root {
    --user-primary-color: #007bff;
    --admin-primary-color: #6f42c1;
    --super-primary-color: #dc3545;
}
```

### 클래스 네이밍
- 역할별 prefix: `user-`, `admin-`, `super-`
- 예: `user-login-container`, `admin-bay-card`, `super-stat-card`

## 📝 main.py 서버 URL 설정

User 서비스에 API가 포함되어 있으므로:

```python
# User 서비스 URL
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "https://user.railway.app")
SERVER_URL = f"{DEFAULT_SERVER_URL}/api/save_shot"
ACTIVE_USER_API = f"{DEFAULT_SERVER_URL}/api/active_user"
```

## ✅ 완료된 작업

- [x] 역할별 서비스 분리
- [x] 타석 코드 매칭 기능
- [x] CSS 파일 분리
- [x] 데이터베이스 확장 (payments, subscriptions)
- [x] 권한 미들웨어 구현
- [x] 템플릿 파일 생성

## 🎯 다음 단계

1. Railway에 각 서비스 배포
2. PostgreSQL 연결 설정
3. 환경 변수 설정
4. main.py 서버 URL 업데이트
5. 테스트
