# 샷 데이터 기록 테스트 가이드

## 테스트 시나리오
- **유저**: A유저
- **매장**: TESTID
- **타석**: 1번 타석 (01)

## 사전 준비

### 1. A유저 계정 생성
1. 유저 웹 서비스 접속: `https://golf-user-web-production-*.up.railway.app/signup`
2. 회원가입 정보 입력:
   - 이름: A유저
   - 휴대폰번호: (자유 입력, 이게 user_id가 됨)
   - 생년월일, 성별, 비밀번호 입력
3. 회원가입 완료

### 2. TESTID 매장 확인
- TESTID 매장이 이미 등록되어 있는지 확인
- 없으면 매장 등록 필요

### 3. 샷 수집 프로그램 설정

#### `config.json` 파일 수정
샷 수집 프로그램이 실행되는 PC의 `config.json` 파일에 다음을 추가:

```json
{
  "auto_brand": "sg골프",
  "auto_filename": "sg골프 v3",
  "store_id": "TESTID",
  "bay_id": "01"
}
```

**위치**: 샷 수집 프로그램(`GolfShotTracker.exe`)과 같은 폴더에 `config/config.json` 파일 생성/수정

## 테스트 절차

### Step 1: 유저 로그인 및 타석 선택
1. 유저 웹 서비스 접속: `https://golf-user-web-production-*.up.railway.app/login`
2. A유저로 로그인 (휴대폰번호/비밀번호)
3. 매장 선택: **TESTID**
4. 타석 선택: **01번 타석**
5. "확인" 버튼 클릭
   - → 활성 세션이 등록됨 (`active_sessions` 테이블에 기록)

### Step 2: 샷 수집 프로그램 실행
1. 샷 수집 프로그램(`GolfShotTracker.exe`) 실행
2. 프로그램이 `config.json`에서 `store_id="TESTID"`, `bay_id="01"`을 읽어옴
3. 프로그램이 `/api/active_user?store_id=TESTID&bay_id=01` API를 호출
4. A유저가 활성 세션에 있으면 → `user_id` 반환
5. 샷이 감지되면 → `user_id`가 A유저로 저장됨

### Step 3: 샷 기록 확인
1. 샷 수집 프로그램에서 샷을 감지하면:
   - 로그에 `👤 현재 활성 사용자: A유저` 표시
   - 서버로 전송 시 `"user_id": "A유저"` 포함
2. 매장 관리자 페이지에서 확인:
   - `https://golf-store-admin-production-*.up.railway.app/login`
   - TESTID 매장 로그인
   - "01번 타석" → "샷 기록 보기" 클릭
   - A유저의 샷 데이터가 기록되어 있는지 확인
3. 유저 페이지에서 확인:
   - A유저 로그인 상태에서 "전체 샷 기록 보기"
   - TESTID 매장 01번 타석의 샷 데이터 확인

## 예상 동작

### 정상 동작
1. ✅ A유저가 로그인하고 TESTID 01번 타석 선택
2. ✅ 샷 수집 프로그램이 `get_active_user("TESTID", "01")` 호출
3. ✅ API가 `{"user_id": "A유저"}` 반환
4. ✅ 샷 감지 시 `user_id: "A유저"`로 저장
5. ✅ 매장 관리자/유저 페이지에서 A유저의 샷 데이터 확인 가능

### 비정상 동작 (게스트로 저장되는 경우)
1. ❌ A유저가 로그인하지 않음 → `user_id: "GUEST"`로 저장
2. ❌ 다른 타석을 선택함 → `user_id: "GUEST"`로 저장
3. ❌ `config.json`의 `store_id`/`bay_id`가 잘못됨 → `user_id: "GUEST"`로 저장

## 문제 해결

### 문제 1: 샷이 게스트로 저장됨
**원인**: 활성 세션이 없거나 `store_id`/`bay_id`가 일치하지 않음

**해결**:
1. 유저가 정확히 TESTID 매장 01번 타석을 선택했는지 확인
2. `config.json`의 `store_id`와 `bay_id` 확인
3. 샷 수집 프로그램 로그에서 `👤 현재 활성 사용자:` 메시지 확인

### 문제 2: API 호출 실패
**원인**: 서버 연결 문제

**해결**:
1. 샷 수집 프로그램 로그에서 `⚠️ 활성 사용자 조회 실패:` 메시지 확인
2. 서버 URL 확인: `https://golf-api-production-e675.up.railway.app`

### 문제 3: 샷 데이터가 저장되지 않음
**원인**: 샷 감지 실패 또는 서버 전송 실패

**해결**:
1. 샷 수집 프로그램 로그에서 `[SHOT CONFIRMED]` 메시지 확인
2. `✅ 서버 전송 성공` 메시지 확인
3. 서버 로그 확인

## 확인 사항 체크리스트

- [ ] A유저 계정 생성 완료
- [ ] TESTID 매장 존재 확인
- [ ] `config.json`에 `store_id: "TESTID"`, `bay_id: "01"` 설정
- [ ] A유저 로그인 및 TESTID 01번 타석 선택 완료
- [ ] 샷 수집 프로그램 실행 및 활성 사용자 조회 성공
- [ ] 샷 감지 및 서버 전송 성공
- [ ] 매장 관리자 페이지에서 샷 데이터 확인
- [ ] 유저 페이지에서 샷 데이터 확인
