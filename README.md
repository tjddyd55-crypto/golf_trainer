# Golf Trainer - 스크린골프 샷 데이터 관리 시스템

## 프로젝트 소개
스크린골프 연습장에서 사용하는 샷 데이터 자동 수집 및 분석 시스템

## 기술 스택
- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **OCR**: Tesseract, OpenCV
- **배포**: Railway

## 로컬 개발 환경 설정

### 1. 저장소 클론
```bash
git clone https://github.com/YOUR_USERNAME/golf_trainer.git
cd golf_trainer
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 데이터베이스 초기화
```bash
python database.py
```

### 5. 서버 실행
```bash
python app.py
```

서버가 `http://localhost:5000`에서 실행됩니다.

## 🚀 빠른 시작

### 배포 가이드
- **빠른 시작**: [QUICK_START.md](QUICK_START.md) - 5단계로 배포하기
- **전체 배포 가이드**: [GITHUB_DEPLOY.md](GITHUB_DEPLOY.md) - 상세 가이드
- **서버 세팅**: [SERVER_SETUP.md](SERVER_SETUP.md) - 서버 설정 가이드
- **체크리스트**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 배포 확인
- **Git 커밋**: [GIT_COMMIT.md](GIT_COMMIT.md) - Git 설정 및 푸시

### 서버 세팅 (Railway)
1. GitHub에 코드 푸시 (자세한 내용: [GIT_COMMIT.md](GIT_COMMIT.md))
2. Railway에서 프로젝트 생성 및 배포 (자세한 내용: [GITHUB_DEPLOY.md](GITHUB_DEPLOY.md))
3. PostgreSQL 서비스 추가
4. 클라이언트 서버 URL 변경

### 주요 단계:
1. GitHub 저장소에 코드 푸시
2. Railway에서 프로젝트 생성 및 배포
3. PostgreSQL 서비스 추가
4. 환경 변수 설정
5. 클라이언트 서버 URL 변경

---

## Railway 배포 가이드

### 1. GitHub에 푸시
```bash
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/golf_trainer.git
git push -u origin main
```

### 2. Railway 배포
1. [Railway](https://railway.app) 접속
2. "New Project" → "Deploy from GitHub repo"
3. `golf_trainer` 저장소 선택
4. 자동 배포 시작

### 3. 환경 변수 설정 (Railway 대시보드)
- `PORT`: 자동 설정됨 (Railway가 제공)
- `FLASK_DEBUG`: `false` (프로덕션)
- `FLASK_SECRET_KEY`: 보안을 위한 시크릿 키 (선택사항)

### 4. PostgreSQL 데이터베이스 설정
이 프로젝트는 PostgreSQL을 사용합니다.

**Railway에서 PostgreSQL 설정**:
1. Railway 대시보드에서 프로젝트 선택
2. "New" 버튼 클릭 → "Database" → "Add PostgreSQL" 선택
3. PostgreSQL 서비스가 자동으로 생성되고 `DATABASE_URL` 환경 변수가 자동 설정됩니다

**로컬 개발 환경에서 PostgreSQL 설정**:
- PostgreSQL을 로컬에 설치하고 데이터베이스를 생성한 후
- `.env` 파일에 `DATABASE_URL=postgresql://user:password@localhost:5432/golf_data` 설정
- 또는 `database.py`의 `DATABASE_URL` 기본값을 수정

### 5. 배포 확인
Railway가 자동으로 배포를 시작합니다. 배포 완료 후 제공된 URL로 접속 가능합니다.

## 프로젝트 구조
```
golf_trainer/
├── app.py                 # Flask 웹 서버
├── main.py               # OCR 클라이언트 (골프 PC에서 실행)
├── database.py           # 데이터베이스 관리
├── calibrate_regions.py  # OCR 영역 캘리브레이션
├── config/               # 설정 파일
│   ├── criteria.json
│   └── feedback_messages.json
├── regions/              # OCR 영역 좌표
│   └── test.json
├── templates/            # HTML 템플릿
├── requirements.txt      # Python 의존성
├── Procfile              # Railway 배포 설정
├── railway.json          # Railway 설정
└── README.md
```

## 주의사항
- `main.py`는 골프 컴퓨터에서 로컬로 실행되는 클라이언트입니다
- `app.py`는 Railway 서버에서 실행되는 웹 서버입니다
- 골프 컴퓨터의 `main.py`에서 서버 URL을 Railway URL로 변경해야 합니다

## 관련 문서
- [Windows 실행 파일 빌드 가이드](README_BUILD.md)
- [OCR 영역 설정 가이드](README_region_setup.md)

## 라이선스
[라이선스 정보]
