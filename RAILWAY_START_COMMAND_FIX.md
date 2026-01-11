# Railway Start Command 설정 가이드

## 문제
Railway Settings에서 Start Command가 보이지 않음

## 해결 방법

### 방법 1: Procfile 자동 인식 (권장)
Railway는 `Procfile`을 자동으로 읽습니다.
- `services/api/Procfile` 파일이 있으면 자동으로 사용됨
- Start Command를 수동으로 설정할 필요 없음

### 방법 2: Railway.json 설정
`railway.json` 파일에 Start Command가 정의되어 있으면 자동으로 사용됩니다.

### 방법 3: Railway Settings에서 수동 설정
1. Railway 대시보드 → 서비스 선택
2. **Settings** 탭
3. **Deploy** 섹션
4. **Start Command** 필드에 입력:
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT
   ```

---

## 각 서비스별 Start Command

### API 서비스
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

### User 서비스
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

### Store Admin 서비스
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

### Super Admin 서비스
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## 확인 사항

### Procfile 확인
각 서비스 디렉토리에 `Procfile`이 있는지 확인:
- [ ] `services/api/Procfile`
- [ ] `services/user/Procfile`
- [ ] `services/store_admin/Procfile`
- [ ] `services/super_admin/Procfile`

### Procfile 내용
각 Procfile에 다음 내용이 있어야 함:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## Railway에서 확인

1. **Settings** → **Deploy** 섹션
2. **Start Command** 필드 확인
   - 비어 있으면 → Procfile 사용
   - 값이 있으면 → 해당 명령어 사용

### Procfile이 인식되지 않는 경우
1. **Settings** → **Deploy**
2. **Start Command** 필드에 직접 입력
3. **Save** 클릭
