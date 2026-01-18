# 배포 시 원복 문제 원인 조사 보고서

**조사 일시**: 2026-01-19  
**문제**: 코드 변경 후 배포 시 원복되는 현상

---

## 1️⃣ Railway 배포 브랜치/커밋 SHA 확인

### 현재 Git 상태
- **활성 브랜치**: `main`
- **최근 커밋**: `e81c5df` - "Fix: format_bay_display 함수 원복 - bay_id 우선"
- **이전 커밋**: `2bfcf02`, `c94d165`, `69e74c1`, `3cbf46f` 등

### Railway 설정 파일
- `railway.json` (루트): NIXPACKS 빌더, gunicorn 시작 명령
- `railway.toml`: 동일 설정
- **각 서비스별 별도 railway.json 존재**:
  - `services/user/railway.json`
  - `services/super_admin/railway.json`
  - `services/store_admin/railway.json`
  - `services/api/railway.json`

### ⚠️ 확인 필요 사항
**Railway 대시보드에서 실제 확인 필요**:
1. 각 서비스가 어떤 Git 브랜치를 보고 있는지
2. 배포된 최신 커밋 SHA가 `e81c5df`인지
3. Production/Staging 환경 구분 여부

---

## 2️⃣ select-store-bay 템플릿 렌더링 위치 추적

### 템플릿 위치
- **파일 경로**: `services/user/templates/select_store_bay.html` (단일 파일)

### 렌더링 위치
- **라우트**: `@app.route("/select-store-bay", methods=["GET", "POST"])`
- **함수**: `select_store_bay()` in `services/user/app.py:112`
- **렌더링 호출**: `render_template("select_store_bay.html", stores=stores)` (5곳)

### 템플릿 내용 (bay_name 표시)
```javascript
// line 107-123
data.bays.forEach(bay => {
    const option = document.createElement('option');
    option.value = bay.bay_id;
    // bay_name이 있으면 우선 사용 (PC 등록 시 입력한 값), 없으면 bay_id 사용
    if (bay.bay_name && bay.bay_name.trim()) {
        option.textContent = bay.bay_name;  // ✅ 유저 화면: bay_name 우선
    } else {
        // bay_id 사용 로직...
    }
});
```

### ✅ 결론
- 템플릿은 **단일 파일**로 존재
- **유저 화면에서만** `bay_name` 우선 표시 사용
- 관리자/매장 관리자 템플릿은 별도 파일 (`manage_all_pcs.html`, `manage_pcs.html`)

---

## 3️⃣ DB 초기화/시드 데이터 확인

### init_db() 함수 위치
- `services/super_admin/shared/database.py:28`

### ⚠️ 발견된 문제

#### 3-1. 기본 매장/타석 자동 생성 (line 325-364)
```python
# 기본 매장 생성
cur.execute("SELECT COUNT(*) AS c FROM stores WHERE store_id = %s", ("gaja",))
row = cur.fetchone()
if not row or row[0] == 0:
    cur.execute(
        "INSERT INTO stores (store_id, store_name, admin_pw, bays_count) VALUES (%s, %s, %s, %s)",
        ("gaja", "가자골프", "1111", 5),  # ⚠️ 하드코딩된 기본 매장
    )
    # 기본 타석 생성 (1~5번 타석)
    for i in range(1, 6):
        bay_id = f"{i:02d}"
        # ...
```

**문제점**:
- `init_db()` 호출 시마다 "gaja" 매장이 없으면 **자동 생성**
- `bays_count=5`로 고정되어 **1~5번 타석 자동 생성**

#### 3-2. init_db() 호출 위치
- `services/super_admin/app.py:34` - `database.init_db()`
- **앱 시작 시마다 실행**됨

### 🔥 핵심 문제
**Railway 서버 재시작 시**:
1. `init_db()` 실행
2. "gaja" 매장 없음 → 자동 생성
3. 타석 1~5번 자동 생성
4. **삭제한 매장/타석이 다시 생성됨**

---

## 4️⃣ DATABASE_URL 환경변수 확인

### 확인 필요 사항
**Railway 대시보드에서 확인 필요**:
1. 각 서비스의 `DATABASE_URL` 환경변수
2. 로컬 개발 환경과 Railway의 DB가 **동일한지** 확인
3. Production/Staging DB 분리 여부

### 코드 내 DB 연결
- `get_db_connection()` 함수가 `DATABASE_URL` 사용
- 각 서비스별로 동일한 `shared/database.py` 사용 가능성

---

## 5️⃣ 삭제 API Soft/Hard Delete 확인

### delete_store() 함수 (line 1354-1412)
```python
def delete_store(store_id):
    """매장 삭제 (모든 관련 데이터 포함)"""
    # ...
    # 관련 데이터 삭제 (순서 중요: 외래키 참조 제거)
    cur.execute("DELETE FROM active_sessions WHERE store_id = %s", (store_id,))
    cur.execute("DELETE FROM bays WHERE store_id = %s", (store_id,))
    cur.execute("DELETE FROM shots WHERE store_id = %s", (store_id,))
    cur.execute("DELETE FROM store_pcs WHERE store_id = %s", (store_id,))
    # 매장 삭제
    cur.execute("DELETE FROM stores WHERE store_id = %s", (store_id,))
```

### ✅ 결론
- **Hard Delete** 사용 (완전 삭제)
- `deleted_at`, `is_active` 플래그 **없음**
- `DELETE FROM` 직접 실행

---

## 🔥 원인 추정

### 가장 가능성 높은 원인: **init_db() 자동 생성 로직**

**시나리오**:
1. 사용자가 매장/타석 삭제 (Hard Delete)
2. Railway 서버 재시작 또는 배포
3. `init_db()` 실행
4. "gaja" 매장이 없으므로 **자동으로 다시 생성**
5. 타석 1~5번도 자동 생성
6. **결과: 삭제한 데이터가 다시 나타남**

---

## 📋 확인 체크리스트

### Railway 대시보드에서 반드시 확인:
- [ ] 각 서비스(Super Admin, User, Store Admin)의 Git 브랜치 설정
- [ ] 배포된 최신 커밋 SHA (`e81c5df` 포함 여부)
- [ ] `DATABASE_URL` 환경변수 값
- [ ] 로컬과 Railway의 DB가 동일한지

### 코드 레벨에서 확인:
- [x] `init_db()` 자동 생성 로직 확인 (문제 발견)
- [x] 삭제 API가 Hard Delete 확인 (확인됨)
- [x] 템플릿 렌더링 위치 확인 (단일 파일)

---

## 💡 해결 방안 (확인 후 실행)

### 방안 1: init_db() 자동 생성 로직 제거/조건 강화
- "gaja" 매장 자동 생성 제거
- 또는 `ENVIRONMENT` 변수로 제어 (개발 환경에서만 생성)

### 방안 2: Soft Delete로 변경
- `deleted_at` 컬럼 추가
- `is_active` 플래그 사용
- 조회 시 `WHERE deleted_at IS NULL` 필터링

### 방안 3: DB 마이그레이션 분리
- `init_db()`는 테이블 생성만
- 시드 데이터는 별도 스크립트로 실행

---

**다음 단계**: Railway 대시보드에서 배포 브랜치/커밋 SHA 확인 필요
