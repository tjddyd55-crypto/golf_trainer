# 최종 서비스 분리 구조

## ✅ 완료된 작업

### 1. 역할별 서비스 분리
- ✅ Super Admin 서비스 (총책임자)
- ✅ Store Admin 서비스 (매장 관리자)
- ✅ User 서비스 (유저 + API)

### 2. 타석 코드 매칭 기능
- ✅ 타석 코드 자동 생성 (4자리: 영문1자 + 숫자3자)
- ✅ 코드로 매장-타석 자동 매칭
- ✅ 유저 로그인 시 코드 입력 기능

### 3. CSS 파일 분리
- ✅ `static/css/user.css` - 유저 서비스
- ✅ `static/css/store_admin.css` - 매장 관리자
- ✅ `static/css/super_admin.css` - 총책임자
- ✅ CSS 변수 사용으로 웹디자이너 수정 용이

### 4. 데이터베이스 확장
- ✅ `payments` 테이블 (결제 관리)
- ✅ `subscriptions` 테이블 (구독 관리)
- ✅ `stores` 테이블 확장 (구독 정보)
- ✅ `bays` 테이블 확장 (타석 코드)

### 5. 권한 미들웨어
- ✅ `shared/auth.py` - 역할 기반 접근 제어
- ✅ `require_role()` 데코레이터
- ✅ `require_login()` 데코레이터

## 📁 최종 디렉토리 구조

```
golf_trainer/
├── services/
│   ├── super_admin/          # 총책임자 서비스
│   │   ├── app.py
│   │   ├── utils.py
│   │   ├── Procfile
│   │   └── templates/
│   ├── store_admin/          # 매장 관리자 서비스
│   │   ├── app.py
│   │   ├── utils.py
│   │   ├── Procfile
│   │   └── templates/
│   ├── user/                 # 유저 서비스 (API 포함)
│   │   ├── app.py
│   │   ├── utils.py
│   │   ├── Procfile
│   │   └── templates/
│   └── api/                  # 공통 API (선택사항)
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

### 옵션 1: 각 서비스를 별도 프로젝트로 배포 (권장)

#### Super Admin 서비스
1. Railway에서 새 프로젝트 생성: `golf-trainer-super-admin`
2. GitHub 저장소 연결
3. 루트 디렉토리: `services/super_admin`
4. Procfile 자동 인식 또는 수동 설정

#### Store Admin 서비스
1. Railway에서 새 프로젝트 생성: `golf-trainer-store-admin`
2. GitHub 저장소 연결
3. 루트 디렉토리: `services/store_admin`
4. Procfile 자동 인식

#### User 서비스
1. Railway에서 새 프로젝트 생성: `golf-trainer-user`
2. GitHub 저장소 연결
3. 루트 디렉토리: `services/user`
4. Procfile 자동 인식

### 옵션 2: 하나의 프로젝트에 여러 서비스

Railway 프로젝트에서:
1. 첫 번째 서비스: Super Admin (루트: `services/super_admin`)
2. 두 번째 서비스: Store Admin (루트: `services/store_admin`)
3. 세 번째 서비스: User (루트: `services/user`)

## 🔑 타석 코드 기능

### 코드 생성
- 매장 등록 시 자동 생성
- 형식: 매장 ID 첫 글자 + 타석 번호
- 예: `gaja` 매장 `01`번 타석 → `G001`

### 코드 사용
1. 타석 앞에 4자리 코드 표시
2. 유저가 앱에서 코드 입력
3. 자동으로 매장-타석 매칭
4. 세션 연결

### API
```
POST /api/check_bay_code
{
    "bay_code": "G001"
}

응답:
{
    "valid": true,
    "store_id": "gaja",
    "bay_id": "01"
}
```

## 🎨 CSS 구조

### 파일 위치
- `static/css/user.css` - 유저 서비스
- `static/css/store_admin.css` - 매장 관리자
- `static/css/super_admin.css` - 총책임자

### CSS 변수
각 파일에서 `:root`에 색상 변수 정의:
```css
:root {
    --user-primary-color: #007bff;
    --admin-primary-color: #6f42c1;
    --super-primary-color: #dc3545;
}
```

### 클래스 네이밍
- 역할별 prefix: `user-`, `admin-`, `super-`
- 예: `user-login-container`, `admin-bay-card`

## 📝 main.py 서버 URL 설정

User 서비스에 API가 포함되어 있으므로:

```python
# User 서비스 URL
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "https://user.railway.app")
SERVER_URL = f"{DEFAULT_SERVER_URL}/api/save_shot"
ACTIVE_USER_API = f"{DEFAULT_SERVER_URL}/api/active_user"
```

## ✅ 체크리스트

### 서비스 분리
- [x] Super Admin 서비스 생성
- [x] Store Admin 서비스 생성
- [x] User 서비스 생성
- [x] 공유 모듈 (database, auth) 생성

### 타석 코드 기능
- [x] 데이터베이스에 bay_code 필드 추가
- [x] 코드 생성 함수 구현
- [x] 코드로 매장-타석 조회 함수 구현
- [x] 유저 로그인에 코드 입력 기능 추가
- [x] 코드 확인 API 구현

### CSS 분리
- [x] user.css 생성
- [x] store_admin.css 생성
- [x] super_admin.css 생성
- [x] CSS 변수 사용
- [x] 클래스 네이밍 규칙 적용

### 데이터베이스
- [x] payments 테이블 추가
- [x] subscriptions 테이블 추가
- [x] stores 테이블 확장
- [x] bays 테이블에 bay_code 추가

### 템플릿
- [x] Super Admin 템플릿 생성
- [x] Store Admin 템플릿 생성
- [x] User 템플릿 생성 (CSS 분리 버전)

## 🎯 다음 단계

1. GitHub에 코드 푸시
2. Railway에 각 서비스 배포
3. PostgreSQL 연결 설정
4. 환경 변수 설정
5. main.py 서버 URL 업데이트
6. 테스트
