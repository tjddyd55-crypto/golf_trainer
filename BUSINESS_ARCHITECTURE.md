# 실무 비즈니스 아키텍처 구성

3단계 역할 구조에 맞춘 최적의 시스템 구성입니다.

---

## 🎯 역할 구조

### 1. 총책임자 (Super Admin / 종합관리자)
- **권한**: 전체 시스템 관리
- **기능**:
  - 매장 등록/관리
  - 매장 결제 관리
  - 사용기간 관리
  - 매장별 통계 조회
  - 전체 통계 대시보드

### 2. 매장사장 (Store Admin / 매장관리자)
- **권한**: 본인 매장만 관리
- **기능**:
  - 본인 매장 대시보드
  - 유저 관리/설정
  - 타석 관리
  - 매장별 샷 데이터 조회
  - 매장 설정

### 3. 유저 (User)
- **권한**: 본인 데이터만 조회
- **기능**:
  - 본인 샷 기록 조회
  - 통계 확인
  - 연습 기록 관리

---

## 🏗️ 최적 구성 제안

### 옵션 1: 단일 서비스 + 역할별 라우팅 (권장 - 초기 단계)

**Railway 구성:**
```
golf_trainer 프로젝트
├── 웹 서비스 1개 (Flask)
│   ├── /super-admin/* (총책임자)
│   ├── /admin/* (매장사장)
│   ├── /user/* (유저)
│   └── /api/* (API)
└── PostgreSQL
```

**장점:**
- ✅ 빠른 개발 및 배포
- ✅ 비용 효율적
- ✅ 단순한 구조
- ✅ 초기 단계에 적합

**단점:**
- ⚠️ 역할별 독립 배포 불가
- ⚠️ 확장성 제한

---

### 옵션 2: 역할별 서비스 분리 (권장 - 성장 단계)

**Railway 구성:**
```
golf_trainer 프로젝트
├── Super Admin 서비스 (Flask)
│   ├── 총책임자 대시보드
│   ├── 매장 관리
│   └── 결제/사용기간 관리
├── Store Admin 서비스 (Flask)
│   ├── 매장 대시보드
│   ├── 유저 관리
│   └── 타석 관리
├── User 서비스 (Flask)
│   ├── 유저 대시보드
│   └── 샷 기록 조회
├── API 서비스 (Flask) - 선택사항
│   └── 공통 API
└── PostgreSQL
```

**장점:**
- ✅ 역할별 독립 배포
- ✅ 권한 관리 명확
- ✅ 확장성 우수
- ✅ 보안 강화

**단점:**
- ⚠️ 복잡도 증가
- ⚠️ 비용 증가 (서비스 3-4개)

---

### 옵션 3: 하이브리드 구성 (권장 - 실무 최적)

**Railway 구성:**
```
golf_trainer 프로젝트
├── 관리자 서비스 (Flask)
│   ├── /super-admin/* (총책임자)
│   └── /admin/* (매장사장)
├── 유저 서비스 (Flask)
│   └── /user/* (유저)
└── PostgreSQL
```

**장점:**
- ✅ 역할별 분리 (관리자/유저)
- ✅ 적절한 복잡도
- ✅ 비용 효율적 (서비스 2개)
- ✅ 실무에 적합

**단점:**
- ⚠️ 관리자 서비스 내부에서 역할 분리 필요

---

## 🎯 실무 권장 구성: 하이브리드 (옵션 3)

### 구조
```
Railway 프로젝트
├── 관리자 서비스 (admin-service)
│   ├── 총책임자 기능
│   │   ├── 매장 관리
│   │   ├── 결제 관리
│   │   ├── 사용기간 관리
│   │   └── 전체 통계
│   └── 매장사장 기능
│       ├── 매장 대시보드
│       ├── 유저 관리
│       └── 타석 관리
├── 유저 서비스 (user-service)
│   └── 유저 기능
│       ├── 샷 기록 조회
│       ├── 통계 확인
│       └── 연습 기록
└── PostgreSQL
```

### 라우팅 구조

#### 관리자 서비스
```
/super-admin/
  ├── /dashboard (총책임자 대시보드)
  ├── /stores (매장 관리)
  ├── /payments (결제 관리)
  ├── /subscriptions (사용기간 관리)
  └── /statistics (전체 통계)

/admin/
  ├── /dashboard (매장 대시보드)
  ├── /users (유저 관리)
  ├── /bays (타석 관리)
  └── /settings (매장 설정)
```

#### 유저 서비스
```
/user/
  ├── /dashboard (유저 대시보드)
  ├── /shots (샷 기록)
  ├── /statistics (통계)
  └── /profile (프로필)
```

---

## 📊 데이터베이스 구조 확장

### 필요한 테이블 추가

```sql
-- 매장 테이블 (기존 확장)
CREATE TABLE stores (
    store_id TEXT PRIMARY KEY,
    store_name TEXT,
    admin_pw TEXT,
    bays_count INTEGER,
    -- 추가 필드
    subscription_status TEXT, -- active, expired, suspended
    subscription_start_date TEXT,
    subscription_end_date TEXT,
    payment_plan TEXT, -- monthly, yearly
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 결제 테이블 (신규)
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    store_id TEXT,
    amount REAL,
    payment_date TEXT,
    payment_method TEXT,
    status TEXT, -- pending, completed, failed
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 사용기간 관리 테이블 (신규)
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    store_id TEXT,
    start_date TEXT,
    end_date TEXT,
    status TEXT, -- active, expired, cancelled
    plan_type TEXT, -- monthly, yearly
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔐 권한 관리 구조

### 세션 구조
```python
# 총책임자 세션
session["role"] = "super_admin"
session["user_id"] = "super_admin_id"

# 매장사장 세션
session["role"] = "store_admin"
session["store_id"] = "gaja"
session["user_id"] = "store_admin_id"

# 유저 세션
session["role"] = "user"
session["user_id"] = "user_id"
session["store_id"] = "gaja"
session["bay_id"] = "01"
```

### 권한 체크 미들웨어
```python
def require_role(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("role")
            if user_role not in allowed_roles:
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 사용 예시
@app.route("/super-admin/dashboard")
@require_role("super_admin")
def super_admin_dashboard():
    ...

@app.route("/admin/dashboard")
@require_role("store_admin")
def store_admin_dashboard():
    ...
```

---

## 🚀 단계별 구현 계획

### Phase 1: 현재 구조 확장 (즉시)
- 기존 단일 서비스 유지
- 라우팅 분리: `/super-admin/*`, `/admin/*`, `/user/*`
- 권한 미들웨어 추가
- 데이터베이스 테이블 확장

### Phase 2: 서비스 분리 (성장 시)
- 관리자 서비스 분리
- 유저 서비스 분리
- API 서비스 분리 (선택사항)

### Phase 3: 고도화 (확장 시)
- 마이크로서비스 아키텍처
- 각 역할별 독립 서비스
- API Gateway 도입

---

## 📝 즉시 적용 가능한 구성

### 현재 단계: 단일 서비스 + 역할별 라우팅

**구조:**
```
웹 서비스 1개
├── /super-admin/* (총책임자)
├── /admin/* (매장사장) - 기존
└── /user/* (유저) - 기존
```

**장점:**
- ✅ 빠른 구현
- ✅ 기존 코드 최대한 활용
- ✅ 단계적 확장 가능

**구현 작업:**
1. `/super-admin/*` 라우팅 추가
2. 결제/사용기간 관리 기능 추가
3. 권한 미들웨어 구현
4. 데이터베이스 테이블 확장

---

## 🎯 결론 및 권장사항

### 초기 단계 (현재)
**단일 서비스 + 역할별 라우팅**
- 빠른 개발
- 비용 효율적
- 실무 적용 가능

### 성장 단계
**하이브리드 구성 (관리자 서비스 + 유저 서비스)**
- 역할별 분리
- 적절한 복잡도
- 실무 최적

### 확장 단계
**완전 분리 (각 역할별 서비스)**
- 최대 확장성
- 독립 배포
- 고도화

---

## 💡 실무 고려사항

### 보안
- 역할별 접근 제어
- API 인증 강화
- 결제 정보 암호화

### 성능
- 역할별 캐싱 전략
- 데이터베이스 인덱싱
- 쿼리 최적화

### 모니터링
- 역할별 사용량 추적
- 결제/구독 모니터링
- 오류 추적

---

## 📋 체크리스트

### Phase 1 구현
- [ ] `/super-admin/*` 라우팅 추가
- [ ] 결제 관리 기능
- [ ] 사용기간 관리 기능
- [ ] 권한 미들웨어 구현
- [ ] 데이터베이스 테이블 확장

### Phase 2 분리
- [ ] 관리자 서비스 분리
- [ ] 유저 서비스 분리
- [ ] 서비스 간 통신 설정

### Phase 3 고도화
- [ ] 마이크로서비스 전환
- [ ] API Gateway 도입
- [ ] 모니터링 시스템 구축
