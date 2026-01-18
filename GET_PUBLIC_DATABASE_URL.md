# Railway PostgreSQL Public Network URL 확인 방법

로컬에서 Railway PostgreSQL에 연결하려면 **Public Network URL**이 필요합니다.

`postgres.railway.internal`은 Railway 내부 전용이므로 로컬에서는 접근할 수 없습니다.

---

## Public Network URL 확인 방법

### 방법 1: Railway PostgreSQL 서비스 Variables 확인

1. **Railway 대시보드 접속**
   - https://railway.app 접속

2. **PostgreSQL 서비스 선택**
   - 프로젝트에서 PostgreSQL 서비스 찾기
   - PostgreSQL 서비스 카드 클릭

3. **Variables 탭 클릭**
   - 서비스 상세 페이지에서 **"Variables"** 탭 클릭

4. **DATABASE_URL 확인**
   - `DATABASE_URL` 변수 찾기
   - 값이 `postgres.railway.internal`로 시작하면 내부 URL
   - **Public Network URL**을 찾아야 합니다

---

### 방법 2: Railway PostgreSQL 서비스 Connect 탭 확인

1. **PostgreSQL 서비스 선택**
   - Railway 대시보드에서 PostgreSQL 서비스 클릭

2. **Connect 탭 클릭**
   - 서비스 상세 페이지에서 **"Connect"** 탭 클릭

3. **Public Network URL 복사**
   - **"Public Network"** 섹션에서 연결 문자열 확인
   - 형식: `postgresql://postgres:password@host.railway.app:5432/railway`
   - 또는 `postgresql://postgres:password@monorail.proxy.rlwy.net:12345/railway`

4. **복사하여 사용**
   - 이 URL을 `DATABASE_URL`로 사용하면 로컬에서 접근 가능

---

### 방법 3: Railway CLI 사용 (프로젝트 연결 후)

```bash
# 프로젝트 연결 (처음 한 번만)
railway link

# 환경 변수 확인
railway variables

# DATABASE_URL 확인
railway variables --json | grep DATABASE_URL
```

---

## ⚠️ 주의사항

1. **내부 URL vs Public URL**
   - `postgres.railway.internal` → Railway 내부 전용 (외부 접근 불가)
   - `host.railway.app` 또는 `monorail.proxy.rlwy.net` → Public Network (외부 접근 가능)

2. **Public Network 활성화**
   - Railway PostgreSQL 서비스에서 Public Network가 활성화되어 있어야 합니다
   - Connect 탭에서 확인 가능

3. **보안**
   - Public Network URL은 비밀번호가 포함되어 있으므로 안전하게 관리하세요
   - 필요 없을 때는 비활성화 권장

---

## Public Network URL 형식

```
postgresql://postgres:PASSWORD@HOST:PORT/railway
```

예시:
- `postgresql://postgres:password@monorail.proxy.rlwy.net:5432/railway`
- `postgresql://postgres:password@postgres-production.up.railway.app:5432/railway`

---

## 빠른 확인 방법

Railway 대시보드에서:
1. PostgreSQL 서비스 클릭
2. **Connect** 탭 클릭
3. **Public Network** 섹션 확인
4. 연결 문자열 복사

이 URL을 `DATABASE_URL`로 사용하면 로컬에서 접근 가능합니다!
