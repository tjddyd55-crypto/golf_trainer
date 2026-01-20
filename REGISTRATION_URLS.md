# 등록 프로그램 및 URL 가이드

## 1. PC 등록 프로그램 (EXE)

### 실행 파일 위치
```
dist/register_pc_gui.exe
```

### 사용 방법
1. `dist/register_pc_gui.exe` 파일을 각 타석 PC에 복사
2. 더블클릭하여 실행
3. 다음 정보 입력:
   - **PC 등록 코드**: 슈퍼 관리자가 발급한 등록 코드
   - **매장명**: 매장 이름 (예: "테스트매장")
   - **타석(룸)명**: 타석 이름 (예: "1번룸", "01번 타석")
   - **타석(룸) 이름**: PC 이름 (예: "1번방", "1번룸")
   - **서버 URL**: 기본값 사용 (엔터)
4. "등록 요청" 버튼 클릭
5. 슈퍼 관리자 승인 대기

---

## 2. 매장 등록 (웹 기반)

### 매장 등록 URL
```
https://golf-store-admin-production.up.railway.app/signup
```

### 사용 방법
1. 위 URL에 접속
2. 다음 정보 입력:
   - **매장코드**: 영문 대문자로 시작, 영문자와 숫자만 사용 (4-10자)
   - **비밀번호**: 매장 관리자 비밀번호
   - **비밀번호 확인**: 비밀번호 재입력
   - **매장명**: 매장 이름
   - **연락처**: 매장 연락처
   - **사업자등록번호**: 사업자등록번호 (선택)
   - **타석(룸) 수**: 1개 이상 50개 이하
   - **대표자명**: 대표자 이름 (선택)
   - **생년월일**: 생년월일 (선택)
   - **이메일**: 이메일 주소 (선택)
   - **주소**: 매장 주소 (선택)
3. "매장 등록" 버튼 클릭
4. "매장 등록 요청이 완료되었습니다. 승인 대기 중입니다." 메시지 확인
5. 슈퍼 관리자 승인 대기

---

## 3. 슈퍼 관리자 승인

### 매장 등록 요청 승인 URL
```
https://golf-super-admin-production.up.railway.app/store-requests
```

### PC 등록 승인 URL
```
https://golf-super-admin-production.up.railway.app/pcs
```

### 사용 방법
1. 슈퍼 관리자로 로그인
2. **매장 등록 요청 승인**:
   - `/store-requests` 페이지에서 승인 대기 중인 매장 확인
   - "승인" 버튼 클릭
   - 타석 수 확인 및 승인 완료
3. **PC 등록 승인**:
   - `/pcs` 페이지에서 승인 대기 중인 PC 확인
   - "승인" 버튼 클릭
   - `store_id`, `bay_id` 지정 및 사용기간 설정
   - 승인 완료

---

## 4. 매장 관리자 로그인

### 매장 관리자 로그인 URL
```
https://golf-store-admin-production.up.railway.app/login
```

### 사용 방법
1. 위 URL에 접속
2. 매장코드와 비밀번호 입력
3. "로그인" 버튼 클릭
4. 승인된 매장만 로그인 가능

---

## 5. 전체 서비스 URL 목록

### 프로덕션 환경
- **API 서비스**: `https://golf-api-production-e675.up.railway.app`
- **User 웹 서비스**: `https://golf-user-web-production.up.railway.app`
- **Store Admin 서비스**: `https://golf-store-admin-production.up.railway.app`
- **Super Admin 서비스**: `https://golf-super-admin-production.up.railway.app`

### 주요 엔드포인트
- 매장 등록: `https://golf-store-admin-production.up.railway.app/signup`
- 매장 관리자 로그인: `https://golf-store-admin-production.up.railway.app/login`
- 매장 등록 요청 승인: `https://golf-super-admin-production.up.railway.app/store-requests`
- PC 등록 승인: `https://golf-super-admin-production.up.railway.app/pcs`

---

## 6. 등록 흐름 요약

### 매장 등록 흐름
1. 매장 관리자가 `/signup`에서 매장 등록 요청
2. 상태: `pending` (승인 대기)
3. 슈퍼 관리자가 `/store-requests`에서 승인
4. 상태: `approved` (승인 완료)
5. 매장 관리자가 `/login`에서 로그인 가능

### PC 등록 흐름
1. 각 타석 PC에서 `register_pc_gui.exe` 실행
2. 등록 정보 입력 및 등록 요청
3. 상태: `pending` (승인 대기)
4. 슈퍼 관리자가 `/pcs`에서 승인
5. 상태: `active` (활성화)
6. 샷 수집 프로그램 실행 가능

---

## 7. 문제 해결

### PC 등록 실패
- 서버 URL이 올바른지 확인
- 등록 코드가 유효한지 확인
- 네트워크 연결 확인

### 매장 등록 실패
- 매장코드 형식 확인 (영문 대문자로 시작, 4-10자)
- 이미 사용 중인 매장코드인지 확인
- 필수 항목 모두 입력 확인

### 승인 대기 중
- 슈퍼 관리자에게 승인 요청
- `/store-requests` 또는 `/pcs` 페이지에서 확인
