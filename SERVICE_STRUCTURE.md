# 서비스 분리 구조

## 디렉토리 구조

```
golf_trainer/
├── services/
│   ├── super_admin/
│   │   ├── app.py (Super Admin Flask 앱)
│   │   ├── routes.py
│   │   └── templates/
│   ├── store_admin/
│   │   ├── app.py (Store Admin Flask 앱)
│   │   ├── routes.py
│   │   └── templates/
│   └── user/
│       ├── app.py (User Flask 앱)
│       ├── routes.py
│       └── templates/
├── shared/
│   ├── database.py
│   ├── auth.py (권한 미들웨어)
│   └── utils.py
├── static/
│   ├── css/
│   │   ├── super_admin.css
│   │   ├── store_admin.css
│   │   └── user.css
│   └── js/
└── config/
    ├── criteria.json
    └── feedback_messages.json
```

## Railway 배포 구조

### 옵션 1: 각 서비스를 별도 프로젝트로 배포
- super-admin 프로젝트
- store-admin 프로젝트
- user 프로젝트
- 각각 PostgreSQL 연결

### 옵션 2: 하나의 프로젝트에 여러 서비스로 배포
- golf_trainer 프로젝트
  - super-admin 서비스
  - store-admin 서비스
  - user 서비스
  - PostgreSQL (공유)

## 코드 매칭 기능

### 타석 코드 생성
- 각 타석에 고유 4자리 코드 부여
- 형식: 영문 1자 + 숫자 3자 (예: A001, B123)
- 데이터베이스에 저장

### 유저 앱에서 코드 입력
- 로그인 후 코드 입력 화면
- 코드 입력 시 매장-타석 자동 매칭
- 세션 연결
