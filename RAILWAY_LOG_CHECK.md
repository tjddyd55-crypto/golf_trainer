# Railway 로그 확인 가이드

## Railway 웹 대시보드에서 로그 확인

### 1단계: Railway 접속
- https://railway.app 접속
- 로그인

### 2단계: 프로젝트 선택
- 대시보드에서 "golf_trainer" 프로젝트 선택

### 3단계: 서비스 선택
- "api" 또는 "services/api" 서비스 선택

### 4단계: 로그 확인
- 상단 탭에서 **"Logs"** 또는 **"Deployments"** 클릭
- 최신 배포의 로그 확인

## 확인할 로그 키워드

### 필수 확인 항목
1. `[TRACE][1] fetched store_name =`
   - store_name이 정상적으로 조회되었는지 확인
   - 예: `[TRACE][1] fetched store_name = '테스트매장'`

2. `[TRACE][FINAL] store_name =`
   - INSERT 직전 store_name 값 확인
   - 예: `[TRACE][FINAL] store_name = '테스트매장'`

3. `[TRACE][PARAMS]`
   - INSERT 파라미터 전체 확인
   - 예: `[TRACE][PARAMS] {'store_name': '테스트매장', 'store_id': 'TESTID', ...}`

4. `assert` 에러
   - `AssertionError: invalid store_name` 또는 유사 메시지 확인

5. `psycopg2.errors.NotNullViolation`
   - store_name NULL 에러 확인

## 로그 필터링 방법

### Railway 로그 화면에서
- 검색창에 `TRACE` 입력 → 모든 TRACE 로그 확인
- 검색창에 `store_name` 입력 → store_name 관련 로그만 확인
- 검색창에 `register_pc_new` 입력 → 해당 함수 로그만 확인

## 로그 확인 후 공유할 정보

다음 정보를 공유해주세요:

1. `[TRACE][1] fetched store_name =` 뒤의 값
2. `[TRACE][PARAMS]` 전체 출력
3. assert 에러 발생 여부 (에러 메시지 포함)
4. 에러 발생 시점의 전체 스택 트레이스

## Railway CLI 사용 (선택사항)

```bash
# Railway CLI 설치 (미설치 시)
npm i -g @railway/cli

# 로그인
railway login

# 프로젝트 선택
railway link

# 로그 확인
railway logs

# 특정 키워드 필터링
railway logs | grep "TRACE"
railway logs | grep "store_name"
```
