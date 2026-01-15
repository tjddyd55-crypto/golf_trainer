# 코드 점검: 하드코딩된 값 확인

## ✅ 정상 (동적 처리됨)

### 1. `main.py` - Store ID / Bay ID
```python
def get_store_id():
    """config.json에서 store_id를 읽어오거나 기본값 반환"""
    config = load_config()
    return config.get("store_id") or "gaja"  # ← fallback 기본값

def get_bay_id():
    """config.json에서 bay_id를 읽어오거나 기본값 반환"""
    config = load_config()
    return config.get("bay_id") or "01"  # ← fallback 기본값
```
**상태**: ✅ 정상 - `config.json`에서 동적으로 읽어옴, 기본값은 fallback용

### 2. API URL
```python
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "https://golf-api-production-e675.up.railway.app")
```
**상태**: ✅ 정상 - 환경 변수 또는 기본값 사용

### 3. 슈퍼 관리자 비밀번호
```python
super_admin_password = os.environ.get("SUPER_ADMIN_PASSWORD", "endolpin0!")
```
**상태**: ✅ 수정 완료 - 불일치하던 "admin123" → "endolpin0!"로 통일

## ⚠️ 하드코딩 (의도적)

### 1. `main.py` - Club ID
```python
DEFAULT_CLUB_ID = "Driver"
```
**상태**: ⚠️ 하드코딩됨 (의도적)
**이유**: 현재 시스템이 Driver만 지원하므로 하드코딩이 적절함
**향후**: 다른 클럽 지원 시 `config.json`에서 읽도록 변경 가능

### 2. `main.py` - Fallback 기본값
```python
return config.get("store_id") or "gaja"  # fallback
return config.get("bay_id") or "01"      # fallback
```
**상태**: ⚠️ 하드코딩됨 (의도적 - fallback용)
**이유**: `config.json`이 없을 때를 대비한 기본값
**권장**: 실제 운영 시 `config.json`에 반드시 설정 필요

## 📝 사용자 설정 필요

### `config/config.json`
```json
{
  "auto_brand": "sg골프",
  "auto_filename": "sg골프 v3",
  "store_id": "TESTID",  ← 실제 매장 ID로 변경 필요
  "bay_id": "01",        ← 실제 타석 번호로 변경 필요
  "API_BASE_URL": "https://golf-api-production-e675.up.railway.app"
}
```
**상태**: ⚠️ 테스트용 값이 들어가 있음
**조치**: 실제 운영 시 실제 매장 ID와 타석 번호로 변경 필요

## 🔍 추가 확인 사항

### 1. OCR 설정값
```python
OCR_TIMEOUT_SEC = 1
SESSION_AUTO_LOGOUT_NO_SHOT = 20 * 60  # 20분
SESSION_AUTO_LOGOUT_NO_SCREEN = 5 * 60  # 5분
```
**상태**: ✅ 정상 - 운영 상수값이므로 하드코딩 적절

### 2. GPT 피드백 설정
```python
USE_GPT_FEEDBACK = True
GPT_MODEL = "gpt-4o-mini"
```
**상태**: ✅ 정상 - 기능 플래그 및 모델명이므로 하드코딩 적절

### 3. 샷 간격 체크
```python
MIN_SHOT_INTERVAL = 2.0  # 최소 샷 간격 (초)
```
**상태**: ✅ 정상 - 운영 상수값이므로 하드코딩 적절

## ✅ 최종 점검 결과

### 수정 완료
- ✅ 슈퍼 관리자 비밀번호 기본값 통일 ("admin123" → "endolpin0!")

### 정상 (수정 불필요)
- ✅ Store ID / Bay ID: `config.json`에서 동적 읽기
- ✅ API URL: 환경 변수 또는 기본값 사용
- ✅ 운영 상수값들: 하드코딩 적절

### 사용자 설정 필요
- ⚠️ `config/config.json`의 `store_id`와 `bay_id`를 실제 값으로 변경

## 🎯 테스트 전 체크리스트

- [ ] `config/config.json`의 `store_id`를 실제 매장 ID로 변경
- [ ] `config/config.json`의 `bay_id`를 실제 타석 번호로 변경
- [ ] `config/config.json`의 `auto_brand`와 `auto_filename` 확인
- [ ] Railway 환경 변수 확인 (SUPER_ADMIN_PASSWORD 등)
- [ ] API URL이 올바른지 확인
