# 시스템 테스트 체크리스트

## 완료된 수정 사항

### 1. 문법 오류 수정
- ✅ `shared/database.py`의 중복된 except 블록 제거
- ✅ 모든 서비스의 shared 모듈 동기화

### 2. 누락된 함수 추가
- ✅ `services/super_admin/shared/database.py`에 다음 함수 추가:
  - `get_all_stores()`
  - `get_pending_stores()`
  - `approve_store()`
  - `reject_store()`

### 3. 에러 핸들링 강화
- ✅ 모든 주요 라우트에 try-except 블록 추가
- ✅ 데이터베이스 연결 오류 처리
- ✅ 예외 발생 시 상세한 오류 메시지 및 트레이스백 출력

### 4. RealDictCursor import 수정
- ✅ `services/super_admin/app.py`의 모든 함수에서 `RealDictCursor` 올바르게 import

## 테스트해야 할 주요 기능

### 유저 웹 서비스 (golf-user-web)
1. **메인 페이지** (`/main`)
   - 회원가입/로그인 버튼 표시 확인
   
2. **회원가입** (`/signup`)
   - 이름, 생년월일, 성별, 아이디(휴대폰번호), 비밀번호 입력
   - 휴대폰번호 중복 체크
   
3. **로그인** (`/login`)
   - 아이디(휴대폰번호), 비밀번호 입력
   - 로그인 성공 시 매장/타석 선택 페이지로 이동
   
4. **매장/타석 선택** (`/select-store-bay`)
   - 매장 드롭다운 선택
   - 타석 드롭다운 선택
   - 확인 버튼 클릭
   - 현재 상황 표시 확인
   
5. **대시보드** (`/dashboard`)
   - 매장/타석 이용중 표시
   - 샷 데이터 표시

### 슈퍼 관리자 서비스 (golf-super-admin)
1. **로그인** (`/login`)
   - 환경 변수에서 인증 정보 확인
   
2. **대시보드** (`/`)
   - 매장 목록 표시
   - 통계 정보 표시
   
3. **매장 등록 요청 승인** (`/store-requests`)
   - 승인 대기 목록 표시
   - 승인/거부 기능
   
4. **매장 관리** (`/stores`)
   - 모든 매장 목록 표시

### 매장 관리자 서비스 (golf-store-admin)
1. **회원가입** (`/signup`)
   - 매장 등록 요청 (pending 상태)
   
2. **로그인** (`/login`)
   - 승인된 매장만 로그인 가능
   - pending/rejected 상태 처리
   
3. **대시보드** (`/`)
   - 타석별 활성 사용자 표시
   - 샷 데이터 표시

## 발견된 오류 시 확인 사항

1. **Internal Server Error 발생 시**
   - Railway 로그 확인 (Deployments > View Logs)
   - 에러 메시지 확인
   - 데이터베이스 연결 상태 확인
   - 환경 변수 설정 확인

2. **데이터베이스 오류**
   - `DATABASE_URL` 환경 변수 확인
   - 테이블 존재 여부 확인
   - 컬럼 존재 여부 확인

3. **모듈 import 오류**
   - `shared` 모듈 경로 확인
   - 각 서비스의 `shared` 폴더 확인
   - 함수 시그니처 일치 확인

## 배포 확인

모든 변경사항이 Railway에 배포되었는지 확인:
- `golf-user-web` 서비스
- `golf-store-admin` 서비스
- `golf-super-admin` 서비스
- `golf-api` 서비스

## 다음 단계

테스트 중 발견된 오류를 보고해주시면 즉시 수정하겠습니다.
