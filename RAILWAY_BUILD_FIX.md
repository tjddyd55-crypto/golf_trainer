# Railway Build Failed 해결 가이드

## 문제
4개 서비스 모두 build failed 발생

## 해결 완료
✅ 각 서비스에 `Procfile` 추가
✅ 각 서비스에 `requirements.txt` 추가 (필수 의존성만)
✅ Python 버전 지정 (`runtime.txt`)

---

## Railway 설정 확인 사항

### API 서비스 (golf-api)

#### Settings 확인:
- **Root Directory**: `services/api` ✅
- **Build Command**: (비워둠 - 자동 감지)
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT` ✅

#### 환경 변수:
```
DATABASE_URL=${{golf-trainer-db.DATABASE_URL}}
FLASK_SECRET_KEY=<설정됨>
PORT=5001
FLASK_DEBUG=False
```

#### 확인:
- [ ] `services/api/Procfile` 존재
- [ ] `services/api/requirements.txt` 존재
- [ ] `services/api/app.py` 존재

---

## 추가 확인 사항

### 1. shared 모듈 경로 문제
각 서비스의 `app.py`에서:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from shared import database
```

이 경로는 `services/api`를 Root Directory로 설정했을 때:
- `services/api/../../shared` = `shared/` ✅ (정상)

### 2. static 폴더 경로
```python
static_folder='../../static'
```
- `services/api/../../static` = `static/` ✅ (정상)

### 3. templates 폴더
- 각 서비스는 자체 `templates/` 폴더 사용 ✅

---

## 빌드 실패 원인 체크리스트

### API 서비스
- [ ] Root Directory: `services/api`
- [ ] Procfile 존재: `services/api/Procfile`
- [ ] requirements.txt 존재: `services/api/requirements.txt`
- [ ] app.py 존재: `services/api/app.py`
- [ ] shared 모듈 접근 가능 (루트의 shared/ 폴더)

### User 서비스
- [ ] Root Directory: `services/user`
- [ ] Procfile 존재: `services/user/Procfile`
- [ ] requirements.txt 존재: `services/user/requirements.txt`

### Store Admin 서비스
- [ ] Root Directory: `services/store_admin`
- [ ] Procfile 존재: `services/store_admin/Procfile`
- [ ] requirements.txt 존재: `services/store_admin/requirements.txt`

### Super Admin 서비스
- [ ] Root Directory: `services/super_admin`
- [ ] Procfile 존재: `services/super_admin/Procfile`
- [ ] requirements.txt 존재: `services/super_admin/requirements.txt`

---

## Railway 로그 확인

각 서비스의 **Deployments** 탭에서:
1. 최신 배포 클릭
2. **View Logs** 클릭
3. 오류 메시지 확인

### 일반적인 오류:

#### "No Procfile found"
→ Procfile이 Root Directory에 있는지 확인

#### "ModuleNotFoundError: No module named 'shared'"
→ Root Directory 설정 확인 (services/api 등)

#### "Failed to install dependencies"
→ requirements.txt 확인

---

## 다음 단계

1. GitHub에 푸시 완료 ✅
2. Railway에서 자동 재배포 대기
3. 로그 확인하여 추가 오류 해결
