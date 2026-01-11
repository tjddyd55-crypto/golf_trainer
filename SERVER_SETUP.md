# 서버 세팅 가이드 (Railway 배포)

이 가이드는 로컬 컴퓨터에서 테스트하던 모든 기능을 Railway 서버로 옮기는 과정을 안내합니다.

## 📋 사전 준비 사항

### 1. GitHub 저장소 준비
- [ ] `golf_trainer` 저장소 생성 완료
- [ ] 모든 코드가 GitHub에 푸시됨

### 2. Railway 계정
- [ ] Railway 계정 생성 (https://railway.app)
- [ ] GitHub 계정과 연결

---

## 🚀 1단계: Railway 프로젝트 생성 및 배포

### 1.1 새 프로젝트 생성
1. Railway 대시보드 접속
2. **"New Project"** 클릭
3. **"Deploy from GitHub repo"** 선택
4. `golf_trainer` 저장소 선택
5. 배포 자동 시작 (2-3분 소요)

### 1.2 배포 확인
- Railway 대시보드에서 배포 상태 확인
- **"Deployments"** 탭에서 성공 여부 확인
- 배포 완료 시 서비스 URL 확인 (예: `https://golf-trainer-production.railway.app`)

---

## 🗄️ 2단계: PostgreSQL 데이터베이스 설정

### 2.1 PostgreSQL 서비스 추가
1. Railway 프로젝트 대시보드에서 **"New"** 버튼 클릭
2. **"Database"** 선택
3. **"Add PostgreSQL"** 클릭
4. PostgreSQL 서비스가 자동으로 생성됨

### 2.2 데이터베이스 연결 확인
- PostgreSQL 서비스가 추가되면 `DATABASE_URL` 환경 변수가 **자동으로 설정**됨
- 별도 설정 필요 없음

### 2.3 데이터베이스 초기화
- Flask 앱이 시작되면 `database.init_db()`가 자동 실행되어 테이블 생성
- 또는 Railway CLI를 사용하여 수동 초기화 가능

---

## ⚙️ 3단계: 환경 변수 설정

Railway 대시보드 → 프로젝트 → **"Variables"** 탭에서 다음 환경 변수 설정:

### 필수 환경 변수
- `DATABASE_URL`: PostgreSQL 서비스 추가 시 **자동 설정됨** (수동 설정 불필요)
- `PORT`: Railway가 **자동 설정함** (수동 설정 불필요)

### 선택적 환경 변수 (보안 강화)
- `FLASK_SECRET_KEY`: 시크릿 키 생성 후 설정
  ```bash
  # Python에서 시크릿 키 생성
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  - 생성된 키를 Railway Variables에 추가
  
- `FLASK_DEBUG`: `false` (프로덕션)
  - 기본값: `false` (app.py에서 이미 설정됨)

---

## 🔧 4단계: 서버 접속 테스트

### 4.1 웹 서버 접속 확인
1. Railway에서 제공한 URL로 브라우저 접속
   - 예: `https://your-app.railway.app`
2. 로그인 페이지가 표시되는지 확인

### 4.2 API 엔드포인트 테스트
```bash
# 샷 저장 API 테스트
curl -X POST https://your-app.railway.app/api/save_shot \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "gaja",
    "bay_id": "01",
    "user_id": "test_user",
    "club_id": "Driver",
    "ball_speed": 150.5,
    "club_speed": 100.2,
    "smash_factor": 1.50
  }'
```

---

## 💻 5단계: 클라이언트(main.py) 서버 URL 변경

골프 컴퓨터에서 실행하는 `main.py`의 서버 URL을 Railway URL로 변경해야 합니다.

### 방법 1: 환경 변수 설정 (권장)
```bash
# Windows PowerShell
$env:SERVER_URL="https://your-railway-app.railway.app"
python main.py

# Windows CMD
set SERVER_URL=https://your-railway-app.railway.app
python main.py
```

### 방법 2: 코드 직접 수정
```python
# main.py 상단 부분
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "https://your-railway-app.railway.app")
```

### 방법 3: 배치 파일 생성 (Windows)
`start_client.bat` 파일 생성:
```batch
@echo off
set SERVER_URL=https://your-railway-app.railway.app
python main.py
pause
```

---

## ✅ 6단계: 전체 기능 테스트

### 6.1 사용자 기능 테스트
1. [ ] 회원가입
2. [ ] 로그인
3. [ ] 샷 기록 저장 (main.py 실행)
4. [ ] 샷 기록 조회
5. [ ] 전체 샷 기록 보기

### 6.2 관리자 기능 테스트
1. [ ] 관리자 로그인 (gaja/1111)
2. [ ] 타석 상태 확인
3. [ ] 전체 샷 기록 확인
4. [ ] 타석별 샷 기록 확인

### 6.3 클라이언트 기능 테스트
1. [ ] OCR 영역 인식
2. [ ] 샷 감지 (run text)
3. [ ] 데이터 수집
4. [ ] 서버로 데이터 전송
5. [ ] 음성 피드백 (설정된 경우)

---

## 🔒 7단계: 보안 설정 (프로덕션)

### 7.1 시크릿 키 변경
- Railway Variables에서 `FLASK_SECRET_KEY` 설정
- 기본값 대신 강력한 시크릿 키 사용

### 7.2 CORS 설정 (필요한 경우)
- 클라이언트와 서버 도메인이 다른 경우 CORS 설정 필요

### 7.3 HTTPS 확인
- Railway는 자동으로 HTTPS 제공
- URL이 `https://`로 시작하는지 확인

---

## 🐛 문제 해결

### 데이터베이스 연결 오류
```
psycopg2.OperationalError: could not connect to server
```
- **해결**: Railway에서 PostgreSQL 서비스가 정상적으로 추가되었는지 확인
- `DATABASE_URL` 환경 변수가 자동 설정되었는지 확인

### 배포 실패
- **해결**: Railway 로그 확인
  - 프로젝트 → **"Deployments"** → 실패한 배포 클릭 → 로그 확인
- 의존성 설치 오류인 경우 `requirements.txt` 확인

### 클라이언트에서 서버 연결 실패
- **해결**: 
  1. Railway URL이 정확한지 확인
  2. 방화벽/네트워크 설정 확인
  3. `main.py`의 `SERVER_URL` 환경 변수 확인

---

## 📝 체크리스트 요약

### Railway 설정
- [ ] 프로젝트 생성 및 GitHub 연결
- [ ] 배포 성공 확인
- [ ] 서비스 URL 확인

### 데이터베이스
- [ ] PostgreSQL 서비스 추가
- [ ] `DATABASE_URL` 자동 설정 확인
- [ ] 데이터베이스 테이블 생성 확인

### 환경 변수
- [ ] `FLASK_SECRET_KEY` 설정 (선택사항)
- [ ] `FLASK_DEBUG` 설정 (false)

### 클라이언트 설정
- [ ] `main.py` 서버 URL 변경
- [ ] 환경 변수 설정 또는 코드 수정

### 테스트
- [ ] 웹 서버 접속 확인
- [ ] API 엔드포인트 테스트
- [ ] 사용자 기능 테스트
- [ ] 관리자 기능 테스트
- [ ] 클라이언트 연결 테스트

---

## 🎯 다음 단계

서버 세팅이 완료되면:
1. 로컬 환경에서 Railway 서버로 전환
2. 모든 기능이 정상 작동하는지 확인
3. 프로덕션 환경에서 운영 시작

---

## 📞 참고 자료

- Railway 문서: https://docs.railway.app
- Flask 배포 가이드: https://flask.palletsprojects.com/en/latest/deploying/
- PostgreSQL 연결 가이드: https://www.postgresql.org/docs/
