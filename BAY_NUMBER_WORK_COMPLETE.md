# bay_number 정규화 작업 완료 보고서

## ✅ 완료된 작업 (1-4단계)

### 1. DB/제약조건 정합성 점검 및 보강 ✅

**수정 파일:**
- `services/super_admin/shared/database.py`
- `services/api/shared/database.py`
- `services/user/shared/database.py`
- `services/store_admin/shared/database.py`

**변경 사항:**
- `bays` 테이블에 `bay_number INTEGER` 컬럼 추가
- `bay_name TEXT` 컬럼 추가
- `assigned_pc_unique_id TEXT` 컬럼 추가
- UNIQUE INDEX 생성: `ux_bays_store_baynumber` (store_id, bay_number)

**스키마:**
```sql
CREATE TABLE IF NOT EXISTS bays (
    store_id    TEXT,
    bay_id      TEXT,
    bay_number  INTEGER,  -- ✅ 추가
    bay_name    TEXT,     -- ✅ 추가
    status      TEXT,
    user_id     TEXT,
    last_update TEXT,
    bay_code    TEXT UNIQUE,
    assigned_pc_unique_id TEXT,  -- ✅ 추가
    PRIMARY KEY (store_id, bay_id)
)

CREATE UNIQUE INDEX ux_bays_store_baynumber
ON bays(store_id, bay_number)
WHERE bay_number IS NOT NULL;
```

---

### 2. 서버 API 정리 ✅

**수정 파일:**
- `services/api/app.py`

**추가된 API:**

#### 2-1. 매장 좌석 상태 조회 API
- **Endpoint:** `GET /api/stores/<store_id>/bays`
- **Response:**
```json
{
  "store_id": "A",
  "bays_count": 10,
  "bays": [
    {"bay_number": 1, "bay_name": "1번룸", "assigned": true},
    {"bay_number": 2, "bay_name": null, "assigned": false},
    ...
  ]
}
```

#### 2-2. PC 등록 API (새로운 방식)
- **Endpoint:** `POST /api/pcs/register`
- **Request:**
```json
{
  "store_id": "A",
  "pc_unique_id": "xxx",
  "bay_number": 3,
  "bay_name": "VIP룸"  // optional
}
```
- **Response:**
```json
{
  "ok": true,
  "store_id": "A",
  "bay_id": "...",
  "bay_number": 3,
  "bay_name": "VIP룸"
}
```

**처리 규칙:**
- bay_number 범위 확인 (1..bays_count)
- 중복 확인 (store_id, bay_number) → 409 반환
- bays 테이블에 생성/업데이트
- store_pcs와 연결

---

### 3. PC 등록 프로그램 UI 수정 ✅

**수정 파일:**
- `client/app/pc_register/register_pc_gui.py`

**변경 사항:**
- 타석 입력 필드를 드롭다운으로 변경
- `GET /api/stores/<store_id>/bays` 호출하여 타석 목록 조회
- bays_count 기반으로 드롭다운 생성 (1..N)
- assigned=true 항목은 "(할당됨)" 표시 및 선택 불가 처리
- bay_number 선택 + bay_name 입력 (선택사항)
- `POST /api/pcs/register`로 등록

**UI 표시 규칙:**
- bay_name 있으면: "{bay_number}번 - {bay_name}"
- 없으면: "{bay_number}번 타석(룸)"
- assigned면 뒤에 "(할당됨)"

---

### 4. 관리자/유저 화면 표시 통일 ✅

**수정 파일:**
- `services/super_admin/app.py` - `format_bay_display()` 함수
- `services/store_admin/app.py` - `format_bay_display()` 함수
- `services/user/shared/database.py` - `get_bays()` 함수
- `services/user/templates/select_store_bay.html` - 프론트엔드 표시 로직

**표시 규칙 통일:**
```python
def format_bay_display(bay_number=None, bay_name=None, bay_id=None):
    # bay_name이 있으면 우선 사용
    if bay_name and bay_name.strip():
        return bay_name.strip()
    
    # bay_number가 있으면 번호로 표시
    if bay_number:
        return f"{bay_number}번 타석(룸)"
    
    # bay_id는 내부 키이므로 화면에 출력하지 않음 (레거시 지원만)
    ...
```

**get_bays() 함수:**
- bays 테이블과 store_pcs 조인하여 bay_number, bay_name 포함
- bay_id는 내부 키로만 사용, 화면에 출력하지 않음

---

## 📋 다음 단계 (테스트 필요)

### 5. 샷 수집 정합성 확인
- (store_id, bay_number) → bay_id 매핑 로직 확인 필요
- 샷 저장 시 bay_id 연결 확인 필요

### 6. 실제 스모크 테스트
- PC 등록 드롭다운 테스트
- 유저 타석 선택 화면 테스트
- 샷 저장 정합성 테스트

---

## ⚠️ 주의사항

1. **기존 데이터 마이그레이션 필요**
   - 기존 store_pcs의 bay_id를 bays 테이블의 bay_number로 매핑 필요
   - normalize_bay_ids.py 스크립트 실행 권장

2. **레거시 지원**
   - 기존 bay_id 기반 코드는 레거시로 지원
   - 점진적으로 bay_number로 전환

3. **DB 마이그레이션**
   - 배포 전 DB 마이그레이션 스크립트 실행 필요
   - UNIQUE INDEX 생성 확인

---

## 🎯 완료 조건 체크리스트

- ✅ DB 스키마 수정 (bay_number, bay_name, assigned_pc_unique_id)
- ✅ UNIQUE 제약조건 추가 (store_id, bay_number)
- ✅ 매장 좌석 상태 조회 API 추가
- ✅ PC 등록 API 추가 (bay_number 기반)
- ✅ PC 등록 프로그램 UI 수정
- ✅ 관리자/유저 화면 표시 통일 (bay_name 우선)
- ⏳ 샷 수집 정합성 확인 (테스트 필요)
- ⏳ 실제 스모크 테스트 (테스트 필요)

---

## 📝 배포 전 확인 사항

1. DB 마이그레이션 실행
   - `normalize_bay_ids.py` 실행하여 기존 데이터 정규화
   - UNIQUE INDEX 생성 확인

2. API 테스트
   - `GET /api/stores/<store_id>/bays` 응답 확인
   - `POST /api/pcs/register` 등록 테스트

3. UI 테스트
   - PC 등록 프로그램에서 타석 선택 드롭다운 확인
   - 할당된 타석 "(할당됨)" 표시 확인
   - 유저 화면에서 타석 목록 표시 확인
