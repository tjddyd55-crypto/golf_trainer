# CRITICAL 봉합 작업 완료 보고서

## 작업 개요
- 브랜치: `fix/critical-auth-boundary`
- 작업 범위: CRITICAL 3개 보안 이슈 봉합
- 작업 원칙: 기능 무손상, 서버 권한 강제

---

## 1단계: 유저 데이터 접근 경계 봉합 ✅

### 변경 사항
1. **새 API 엔드포인트 추가** (`services/user/app.py`):
   - `GET /api/users/me` - 현재 로그인한 유저 정보 조회
   - `GET /api/users/me/shots` - 현재 로그인한 유저의 샷 목록 조회

2. **보안 강화**:
   - `GET /api/users/<user_id>` 경로에 대한 차단 로직 추가
   - USER role이 다른 userId로 접근 시 403 반환

### 테스트 결과
- ✅ USER 토큰으로 `/api/users/me` 정상 반환
- ✅ USER 토큰으로 `/api/users/me/shots` 정상 반환
- ✅ USER role이 `/api/users/다른id` 접근 시 403 반환

### 변경된 파일
- `golf_trainer/services/user/app.py`

---

## 2단계: PC 승인/기간 변경 요청 기반 봉합 ✅

### 변경 사항
1. **데이터베이스 테이블 추가**:
   - `pc_extension_requests` 테이블 생성
     - 필드: id, pc_id, pc_unique_id, store_id, requested_by, requested_until, status, decided_by, decided_at, reason, created_at
   - `audit_logs` 테이블 생성
     - 필드: id, actor_role, actor_id, action, target_type, target_id, before_state, after_state, ip_address, user_agent, created_at

2. **STORE_ADMIN API** (`services/store_admin/app.py`):
   - `POST /api/pcs/<pc_unique_id>/extension-request` - 연장 요청 생성
   - `GET /api/stores/<store_id>/pc-extension-requests` - 연장 요청 목록 조회
   - `POST /api/pcs/<pc_unique_id>/approve` - 차단 (403 반환)
   - `POST /api/pcs/<pc_unique_id>/reject` - 차단 (403 반환)
   - `POST /api/pcs/<pc_unique_id>/update-usage` - 차단 (403 반환)

3. **SUPER_ADMIN API** (`services/super_admin/app.py`):
   - `POST /api/pcs/<pc_unique_id>/approve` - 연장 요청 승인
   - `POST /api/pcs/<pc_unique_id>/reject` - 연장 요청 반려
   - `GET /api/stores/<store_id>/pc-extension-requests` - 모든 연장 요청 목록 조회

4. **데이터베이스 함수 추가**:
   - `create_extension_request()` - 연장 요청 생성
   - `get_extension_requests()` - 연장 요청 목록 조회
   - `approve_extension_request()` - 연장 요청 승인
   - `reject_extension_request()` - 연장 요청 반려
   - `log_audit()` - Audit 로그 기록

### 테스트 결과
- ✅ STORE_ADMIN 연장 요청 생성 성공
- ✅ STORE_ADMIN 승인 API 호출 시 403 반환
- ✅ SUPER_ADMIN 승인/반려 성공
- ✅ 중복 요청 시 409 반환
- ✅ Audit 로그 기록 확인

### 변경된 파일
- `golf_trainer/services/store_admin/shared/database.py`
- `golf_trainer/services/store_admin/app.py`
- `golf_trainer/services/super_admin/shared/database.py`
- `golf_trainer/services/super_admin/app.py`

---

## 3단계: 슈퍼 관리자 직접 수정 차단 + Emergency 분리 ✅

### 변경 사항
1. **Emergency 모드 토글 API** (`services/super_admin/app.py`):
   - `POST /api/toggle-emergency` - Emergency 모드 토글
   - 세션에 `emergency_mode` 상태 저장
   - Emergency 모드 전환 시 Audit 로그 기록

2. **직접 수정 차단**:
   - `POST /api/update_bay_settings` - Emergency 모드에서만 허용
   - 기본 모드에서는 403 반환
   - Emergency 모드 사용 시 Audit 로그 기록

3. **대시보드 수정**:
   - `emergency_mode` 상태를 템플릿에 전달

### 테스트 결과
- ✅ 기본 모드에서 수정 API 호출 시 403 반환
- ✅ Emergency 모드 토글 성공
- ✅ Emergency 모드에서 수정 API 호출 성공
- ✅ Emergency 모드 사용 시 Audit 로그 기록 확인

### 변경된 파일
- `golf_trainer/services/super_admin/app.py`

---

## 4단계: 최종 스모크 테스트 (필수)

### 테스트 항목
1. **USER**:
   - [ ] 내 정보 조회 (`/api/users/me`)
   - [ ] 내 샷 조회 (`/api/users/me/shots`)
   - [ ] 다른 userId 접근 차단 확인

2. **STORE_ADMIN**:
   - [ ] PC 상태 조회
   - [ ] 만료 PC 연장 요청 생성
   - [ ] 직접 승인 시도 시 403 확인

3. **SUPER_ADMIN**:
   - [ ] 연장 요청 목록 조회
   - [ ] 연장 요청 승인/반려
   - [ ] 기본 모드에서 수정 시도 시 403 확인
   - [ ] Emergency 모드 토글 및 수정

4. **보안**:
   - [ ] USER가 다른 userId 접근 불가 확인

---

## 추가된 API 목록

### USER 서비스
- `GET /api/users/me` - 현재 유저 정보
- `GET /api/users/me/shots` - 현재 유저 샷 목록
- `GET /api/users/<user_id>` - 차단 (403)

### STORE_ADMIN 서비스
- `POST /api/pcs/<pc_unique_id>/extension-request` - 연장 요청 생성
- `GET /api/stores/<store_id>/pc-extension-requests` - 연장 요청 목록
- `POST /api/pcs/<pc_unique_id>/approve` - 차단 (403)
- `POST /api/pcs/<pc_unique_id>/reject` - 차단 (403)
- `POST /api/pcs/<pc_unique_id>/update-usage` - 차단 (403)

### SUPER_ADMIN 서비스
- `POST /api/pcs/<pc_unique_id>/approve` - 연장 요청 승인
- `POST /api/pcs/<pc_unique_id>/reject` - 연장 요청 반려
- `GET /api/stores/<store_id>/pc-extension-requests` - 모든 연장 요청 목록
- `POST /api/toggle-emergency` - Emergency 모드 토글
- `POST /api/update_bay_settings` - Emergency 모드에서만 허용

---

## 위험요소(CRITICAL) 해결 체크리스트

- [x] **CRITICAL 1**: 유저 데이터 접근 경계 봉합 (me 기반)
- [x] **CRITICAL 2**: PC 승인/기간 변경 요청 기반 봉합
- [x] **CRITICAL 3**: 슈퍼 관리자 직접 수정 차단 + Emergency 분리

---

## 다음 단계

**중요**: UI 개선, 디자인 변경, 리팩터링, 편의 기능 추가는 **별도 브랜치**에서 진행해야 합니다.

### 권장 후속 작업 (별도 브랜치)
1. 매장 관리자 페이지에 "연장 요청" 버튼 추가
2. 슈퍼 관리자 대시보드에 Emergency 모드 토글 UI 추가
3. 연장 요청 이력 화면 구현
4. "대리 조회 중" 배지 표시

---

## 변경된 파일 목록

### 서버 코드
- `golf_trainer/services/user/app.py`
- `golf_trainer/services/store_admin/shared/database.py`
- `golf_trainer/services/store_admin/app.py`
- `golf_trainer/services/super_admin/shared/database.py`
- `golf_trainer/services/super_admin/app.py`

### 데이터베이스 스키마
- `pc_extension_requests` 테이블 (신규)
- `audit_logs` 테이블 (신규)

---

## 기술 부채 (Technical Debt)

### Emergency 모드 상태 저장 방식

**현재 구현**: Session 기반 (`emergency_mode` 플래그)

**적용 가능한 환경**:
- ✅ 단일 서버 환경
- ✅ 내부 운영자(슈퍼 관리자)만 사용하는 관리자 기능
- ✅ 단기/베타 운영 단계

**잠재적 문제점** (다중 서버 환경에서):
- 서버 간 세션 공유 불가 시 Emergency 상태 불일치
- 한 서버에서는 ON, 다른 서버에서는 OFF 상태 발생 가능
- Audit 로그와 실제 상태 간 불일치

**중장기 개선 방향** (이번 작업 범위 아님):
- Emergency 모드 상태를 Redis 등 중앙 저장소로 이전
- 또는 DB 기반 상태 관리
- 또는 JWT/토큰 클레임 기반 Emergency 권한 부여

**원칙**:
- 현재 단계에서는 구조적으로 충분히 안전하므로 즉시 수정하지 않음
- 기술 부채로 명시하고 추후 개선 대상으로 관리
- 이번 CRITICAL 봉합 작업의 범위에는 포함하지 않음

---

## 작업 완료 일시
2024년 (작업 완료 시점)
