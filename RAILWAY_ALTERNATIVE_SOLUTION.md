# Railway Root Directory 변경이 안될 때 해결 방법

## 문제
Railway UI에서 Root Directory 변경이 안됨

## 해결 방법: Procfile 수정 (완료 ✅)

각 서비스의 `Procfile`을 수정했습니다:
- `PYTHONPATH=/app` 추가하여 루트의 `shared` 모듈을 찾을 수 있도록 함
- `cd services/[service]` 추가하여 해당 서비스 디렉토리로 이동

---

## Railway 설정

### 방법 1: Root Directory를 루트로 변경 (가능하면)

각 서비스에서:
- **Root Directory**: `.` (또는 비워둠)

### 방법 2: Root Directory 변경이 안되면

현재 Root Directory가 `services/api`로 설정되어 있어도:
- `Procfile`에서 `cd services/api && PYTHONPATH=/app` 사용
- 하지만 이 방법은 작동하지 않을 수 있음 (이미 services/api 안에 있으므로)

---

## 최종 해결책: 각 서비스 디렉토리에 shared 복사

Root Directory 변경이 불가능한 경우, 각 서비스 디렉토리에 `shared` 폴더를 복사하는 스크립트를 만들거나, 빌드 시 복사하도록 설정해야 합니다.

---

## 현재 상태

✅ `Procfile` 수정 완료
✅ `railway.json` 수정 완료
✅ 코드 수정 완료

⏳ Railway에서 Root Directory를 `.`로 변경해야 함

---

## Railway에서 시도해볼 방법

1. **서비스 삭제 후 재생성** (최후의 수단)
   - 서비스 삭제
   - 같은 저장소에서 다시 생성
   - 생성 시 Root Directory를 `.`로 설정

2. **Railway CLI 사용**
   ```bash
   railway link
   railway variables set ROOT_DIR=.
   ```

3. **Railway 지원팀 문의**
   - Root Directory 변경이 안되는 이유 확인
