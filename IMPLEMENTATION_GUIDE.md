# 서비스 분리 구현 가이드

## 📁 디렉토리 구조

```
golf_trainer/
├── services/
│   ├── super_admin/          # 총책임자 서비스
│   │   ├── app.py
│   │   └── templates/
│   ├── store_admin/          # 매장 관리자 서비스
│   │   ├── app.py
│   │   └── templates/
│   └── user/                 # 유저 서비스
│       ├── app.py
│       └── templates/
├── shared/                   # 공유 모듈
│   ├── database.py
│   └── auth.py
├── static/                   # 정적 파일
│   ├── css/
│   │   ├── user.css
│   │   ├── store_admin.css
│   │   └── super_admin.css
│   └── js/
├── config/                   # 설정 파일
└── main.py                   # 클라이언트 (골프 PC)
```

## 🚀 Railway 배포 방법

### 옵션 1: 각 서비스를 별도 프로젝트로 배포 (권장)

#### 1. Super Admin 서비스
- Railway 프로젝트: `golf-trainer-super-admin`
- 루트 디렉토리: `services/super_admin`
- 시작 명령: `gunicorn app:app --bind 0.0.0.0:$PORT`

#### 2. Store Admin 서비스
- Railway 프로젝트: `golf-trainer-store-admin`
- 루트 디렉토리: `services/store_admin`
- 시작 명령: `gunicorn app:app --bind 0.0.0.0:$PORT`

#### 3. User 서비스
- Railway 프로젝트: `golf-trainer-user`
- 루트 디렉토리: `services/user`
- 시작 명령: `gunicorn app:app --bind 0.0.0.0:$PORT`

### 옵션 2: 하나의 프로젝트에 여러 서비스로 배포

Railway 프로젝트에서:
1. 첫 번째 서비스: Super Admin
2. 두 번째 서비스: Store Admin
3. 세 번째 서비스: User

각 서비스의 루트 디렉토리를 설정:
- Super Admin: `services/super_admin`
- Store Admin: `services/store_admin`
- User: `services/user`

## 🔑 타석 코드 기능

### 코드 형식
- 4자리: 영문 1자 + 숫자 3자
- 예: `A001`, `B123`, `G045`

### 코드 생성
- 매장 등록 시 자동 생성
- 매장 ID의 첫 글자 + 타석 번호

### 코드 사용
1. 타석 앞에 코드 표시 (QR 코드 또는 텍스트)
2. 유저가 앱에서 코드 입력
3. 자동으로 매장-타석 매칭
4. 세션 연결

## 🎨 CSS 구조

### CSS 파일 분리
- `static/css/user.css` - 유저 서비스 스타일
- `static/css/store_admin.css` - 매장 관리자 스타일
- `static/css/super_admin.css` - 총책임자 스타일

### CSS 변수 사용
각 CSS 파일에서 `:root`에 색상 변수 정의:
```css
:root {
    --user-primary-color: #007bff;
    --user-secondary-color: #6c757d;
    /* ... */
}
```

### 클래스 네이밍 규칙
- 역할별 prefix 사용: `user-`, `admin-`, `super-`
- 예: `user-login-container`, `admin-bay-card`, `super-stat-card`

## 📝 다음 단계

1. 나머지 템플릿 파일 생성
2. API 엔드포인트 통합
3. Railway 배포 설정
4. 테스트
