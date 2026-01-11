# GitHub 업로드 및 Railway 배포 가이드

## 📦 1단계: GitHub에 코드 업로드

### GitHub 저장소 생성 (이미 생성했다면 건너뛰기)
1. GitHub (https://github.com) 접속
2. 우측 상단 "+" 버튼 클릭 → "New repository"
3. Repository name: `golf_trainer` (또는 원하는 이름)
4. Visibility: Public 또는 Private 선택
5. "Create repository" 클릭

### 로컬 코드 푸시
현재 디렉토리에서 실행:

```bash
# 원격 저장소 연결 (YOUR_USERNAME을 본인의 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/golf_trainer.git

# 코드 푸시
git push -u origin main
```

또는 GitHub Desktop 사용:
1. GitHub Desktop 실행
2. "Add" → "Add Existing Repository" 선택
3. 현재 프로젝트 폴더 선택
4. "Publish repository" 클릭

---

## 🚂 2단계: Railway 배포

### Railway 프로젝트 생성
1. Railway (https://railway.app) 접속
2. GitHub 계정으로 로그인 (처음이면 가입)
3. "New Project" 클릭
4. "Deploy from GitHub repo" 선택
5. `golf_trainer` 저장소 선택
6. 자동 배포 시작 (2-3분 소요)

### 배포 확인
1. Railway 대시보드에서 배포 상태 확인
2. "Deployments" 탭에서 성공 여부 확인
3. 배포 완료 시 서비스 URL 확인
   - 예: `https://golf-trainer-production.railway.app`

---

## 🗄️ 3단계: PostgreSQL 데이터베이스 추가

### PostgreSQL 서비스 추가
1. Railway 프로젝트 대시보드에서 "New" 버튼 클릭
2. "Database" 선택
3. "Add PostgreSQL" 클릭
4. PostgreSQL 서비스 자동 생성 및 `DATABASE_URL` 환경 변수 자동 설정됨

### 데이터베이스 초기화 확인
- Flask 앱이 시작되면 `database.init_db()`가 자동 실행되어 테이블 생성
- Railway 로그에서 "✅ DB 준비 완료" 메시지 확인

---

## ⚙️ 4단계: 환경 변수 설정 (선택사항)

### 보안 강화를 위한 환경 변수
1. Railway 대시보드 → 프로젝트 선택
2. "Variables" 탭 클릭
3. 다음 환경 변수 추가:

#### FLASK_SECRET_KEY (선택사항, 권장)
시크릿 키 생성:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

생성된 키를 Railway Variables에 추가:
- Variable: `FLASK_SECRET_KEY`
- Value: (생성된 키)

#### FLASK_DEBUG
- Variable: `FLASK_DEBUG`
- Value: `false` (프로덕션)

---

## 💻 5단계: 클라이언트 설정 (골프 컴퓨터)

### Railway 서버 URL 확인
Railway 대시보드에서 서비스 URL 확인:
- 예: `https://golf-trainer-production.railway.app`

### main.py 서버 URL 변경

#### 방법 1: 환경 변수 설정 (권장)
Windows PowerShell:
```powershell
$env:SERVER_URL="https://your-railway-app.railway.app"
python main.py
```

Windows CMD:
```cmd
set SERVER_URL=https://your-railway-app.railway.app
python main.py
```

#### 방법 2: 배치 파일 사용
1. `start_client.bat` 파일 열기
2. `SERVER_URL`에 Railway URL 입력:
   ```batch
   set SERVER_URL=https://your-railway-app.railway.app
   ```
3. 저장 후 더블클릭하여 실행

#### 방법 3: 코드 직접 수정
`main.py` 파일 상단 수정:
```python
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "https://your-railway-app.railway.app")
```

---

## ✅ 6단계: 테스트

### 웹 서버 접속 테스트
1. 브라우저에서 Railway URL 접속
   - 예: `https://golf-trainer-production.railway.app`
2. 로그인 페이지가 표시되는지 확인

### 사용자 기능 테스트
1. 회원가입
2. 로그인
3. 샷 기록 확인

### 관리자 기능 테스트
1. 관리자 로그인 (gaja/1111)
2. 타석 상태 확인
3. 전체 샷 기록 확인

### 클라이언트 연결 테스트
1. 골프 컴퓨터에서 `main.py` 실행
2. OCR 인식 확인
3. 샷 감지 확인
4. 데이터 서버 전송 확인

---

## 🐛 문제 해결

### 배포 실패
- Railway 로그 확인
- `requirements.txt` 의존성 확인
- `Procfile` 형식 확인

### 데이터베이스 연결 오류
- PostgreSQL 서비스 추가 확인
- `DATABASE_URL` 환경 변수 확인

### 클라이언트 연결 실패
- Railway URL 정확성 확인
- 방화벽/네트워크 설정 확인
- HTTPS 사용 확인 (HTTP 아님)

---

## 📞 다음 단계

배포가 완료되면:
1. 프로덕션 환경에서 운영 시작
2. 실제 샷 데이터 수집 시작
3. Railway 대시보드에서 모니터링

---

## 📝 체크리스트

- [ ] GitHub 저장소 생성
- [ ] 코드 푸시 완료
- [ ] Railway 프로젝트 생성
- [ ] 배포 성공 확인
- [ ] PostgreSQL 서비스 추가
- [ ] 환경 변수 설정 (선택사항)
- [ ] 클라이언트 서버 URL 변경
- [ ] 웹 서버 접속 확인
- [ ] 사용자 기능 테스트
- [ ] 관리자 기능 테스트
- [ ] 클라이언트 연결 테스트
