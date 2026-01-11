# Railway 서버로 전환 가이드

로컬 환경에서 Railway 서버로 전환하는 단계별 가이드입니다.

---

## 🚀 1단계: Railway 서버 URL 확인

Railway 서버 URL을 확인하는 방법은 [HOW_TO_FIND_RAILWAY_URL.md](HOW_TO_FIND_RAILWAY_URL.md)를 참고하세요.

### 빠른 확인 방법:
1. Railway 대시보드 접속 (https://railway.app)
2. `golf_trainer` 프로젝트 선택
3. 메인 화면의 서비스 카드에서 URL 확인
   - 예: `https://golf-trainer-production.railway.app`
4. 또는 Settings → Domains에서 확인

**자세한 방법**: [HOW_TO_FIND_RAILWAY_URL.md](HOW_TO_FIND_RAILWAY_URL.md) 참고

---

## 🔧 2단계: 서버 URL 설정

### 방법 1: 자동 설정 스크립트 사용 (권장)

```bash
python switch_to_railway.py
```

스크립트가 다음을 자동으로 업데이트합니다:
- `main.py`의 `DEFAULT_SERVER_URL`
- `start_client.bat`의 `SERVER_URL`

### 방법 2: 수동 설정

#### main.py 수정
```python
# main.py 상단 부분
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "https://your-railway-app.railway.app")
```

#### start_client.bat 수정
```batch
set SERVER_URL=https://your-railway-app.railway.app
```

---

## ✅ 3단계: 서버 연결 테스트

### 자동 테스트 스크립트 사용

```bash
python test_railway_connection.py
```

테스트 항목:
1. 기본 접속 테스트
2. 로그인 페이지 테스트
3. API 엔드포인트 테스트 (active_user)
4. 샷 저장 API 테스트
5. 데이터베이스 연결 테스트 (간접)

### 수동 테스트

1. **브라우저 접속 테스트**
   - Railway URL로 접속
   - 로그인 페이지 표시 확인

2. **API 테스트**
   ```bash
   curl https://your-railway-app.railway.app/api/active_user?store_id=gaja&bay_id=01
   ```

---

## 🧪 4단계: 기능 테스트

### 사용자 기능 테스트
1. 회원가입
2. 로그인
3. 메인 페이지 접속
4. 샷 기록 조회
5. 전체 샷 기록 보기

### 관리자 기능 테스트
1. 관리자 로그인 (gaja/1111)
2. 타석 상태 확인
3. 전체 샷 기록 확인
4. 타석별 샷 기록 확인

### 클라이언트 기능 테스트
1. `start_client.bat` 실행 또는 `python main.py` 실행
2. OCR 영역 인식 확인
3. 샷 감지 확인
4. 데이터 서버 전송 확인
5. 음성 피드백 확인 (설정된 경우)

---

## 📋 5단계: 프로덕션 체크리스트

자세한 체크리스트는 [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)를 참고하세요.

주요 확인 사항:
- [ ] Railway 서버로 전환 완료
- [ ] 서버 연결 테스트 통과
- [ ] 모든 기능 테스트 통과
- [ ] 데이터베이스 정상 작동
- [ ] 보안 설정 완료

---

## 🎯 빠른 시작

### 1. Railway URL 확인
Railway 대시보드에서 서비스 URL 확인

### 2. 서버 URL 설정
```bash
python switch_to_railway.py
```

### 3. 연결 테스트
```bash
python test_railway_connection.py
```

### 4. 클라이언트 실행
```bash
start_client.bat
```

또는:
```bash
set SERVER_URL=https://your-railway-app.railway.app
python main.py
```

---

## 🐛 문제 해결

### 서버 연결 실패
- Railway 대시보드에서 서비스 상태 확인
- URL 정확성 확인 (https:// 포함)
- 방화벽/네트워크 설정 확인

### API 테스트 실패
- Railway 로그 확인
- 데이터베이스 연결 확인
- 환경 변수 확인

### 클라이언트 연결 실패
- `main.py`의 서버 URL 확인
- 환경 변수 `SERVER_URL` 확인
- 네트워크 연결 확인

---

## ✅ 완료 확인

모든 단계를 완료하면:
1. ✅ 로컬 환경에서 Railway 서버로 전환 완료
2. ✅ 모든 기능이 정상 작동 확인
3. ✅ 프로덕션 환경에서 운영 시작 준비 완료

---

## 📞 다음 단계

프로덕션 운영을 시작하려면:
- [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) 참고
- 정기적인 모니터링 설정
- 백업 설정
- 성능 최적화
