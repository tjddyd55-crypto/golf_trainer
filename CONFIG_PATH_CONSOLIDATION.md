# Config 경로 정합 완료 보고서

**작업 일자**: 2026-01-19  
**작업 목적**: `criteria.json` 기준 경로 정리 및 통합  
**상태**: ✅ 완료

---

## 📋 작업 요약

코드 리팩토링은 완료되었으나 `criteria.json` 기준 경로 정리가 미완 상태였습니다.  
이제 모든 경로가 `golf_trainer/config/criteria.json`으로 통일되었습니다.

---

## ✅ 완료된 작업

### 1. 빌드 스크립트 수정
- **파일**: `build_shot_collector_gui.py`
- **변경 사항**:
  - ❌ 제거: `--add-data", "client/state/config;client/state/config"` (사용 안 함)
  - ✅ 추가: `--add-data", "config/criteria.json;config/criteria.json"` (프로젝트 루트 기준)

### 2. 기준 파일 경로 확정
- **기준 파일**: `golf_trainer/config/criteria.json`
- **사용 위치**:
  1. **샷 수집 프로그램 (Client)**: 실행 시 `get_resource_path("config/criteria.json")`으로 번들링된 파일을 실행 경로의 `config/criteria.json`으로 복사
  2. **웹 서비스 (Services)**: `services/user/utils.py`, `services/store_admin/utils.py`에서 프로젝트 루트의 `config/criteria.json` 직접 로드

### 3. 사용하지 않는 경로 확인
- **`client/state/config`**: ❌ 코드에서 사용하지 않음 (제거 가능)
- **빌드 스크립트**: `client/state/config` 번들링 제거 완료

---

## 📁 최종 경로 구조

### 샷 수집 프로그램 (Client)
```
실행 시:
1. 번들링: sys._MEIPASS/config/criteria.json (읽기 전용)
2. 복사: {exe_dir}/config/criteria.json (쓰기 가능)
   → _create_default_config_if_needed()에서 자동 복사
```

**코드 위치**: `client/app/collector/main.py`
```python
BASE_DIR = get_runtime_base_dir()  # exe 실행 시: exe가 있는 폴더
CONFIG_DIR = os.path.join(BASE_DIR, "config")
config_path = os.path.join(CONFIG_DIR, "criteria.json")
```

### 웹 서비스 (Services)
```
프로젝트 루트 기준:
golf_trainer/config/criteria.json
```

**코드 위치**: `services/user/utils.py`, `services/store_admin/utils.py`
```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# → golf_trainer/
CRITERIA_PATH = os.path.join(BASE_DIR, "config", "criteria.json")
# → golf_trainer/config/criteria.json
```

---

## 🔄 빌드 및 실행 흐름

### 빌드 시
1. `build_shot_collector_gui.py` 실행
2. `config/criteria.json` → `sys._MEIPASS/config/criteria.json` (번들링)

### 실행 시
1. `shot_collector_gui.exe` 실행
2. `_create_default_config_if_needed()` 호출
3. `get_resource_path("config/criteria.json")`로 번들링 파일 확인
4. `{exe_dir}/config/criteria.json`이 없으면 번들링 파일 복사
5. 이후 `{exe_dir}/config/criteria.json` 사용

---

## ✅ 검증 사항

| 항목 | 상태 | 비고 |
|------|------|------|
| 기준 파일 통일 | ✅ | `golf_trainer/config/criteria.json` |
| 빌드 스크립트 수정 | ✅ | `client/state/config` 제거 완료 |
| 샷 수집 프로그램 경로 | ✅ | 실행 경로의 `config/criteria.json` 사용 |
| 웹 서비스 경로 | ✅ | 프로젝트 루트의 `config/criteria.json` 사용 |
| 번들링 경로 | ✅ | `config/criteria.json` 번들링 포함 |

---

## 📝 변경 전후 비교

### 변경 전
```python
# build_shot_collector_gui.py
"--add-data", "client/state/config;client/state/config",  # ← 사용 안 함
```

### 변경 후
```python
# build_shot_collector_gui.py
"--add-data", "config/criteria.json;config/criteria.json",  # ← 프로젝트 루트 기준
```

---

## 🎯 최종 정리

### 기준 파일 위치 (단일 소스)
- **`golf_trainer/config/criteria.json`**: 모든 기준의 단일 소스

### 사용 위치
1. **샷 수집 프로그램**: 빌드 시 번들링 → 실행 시 실행 경로로 복사
2. **웹 서비스**: 프로젝트 루트에서 직접 로드

### 제거된 경로
- **`client/state/config`**: 더 이상 사용하지 않음 (빌드 스크립트에서 제거)

---

**결론**: 모든 경로가 `golf_trainer/config/criteria.json`으로 통일되었으며, 빌드 및 실행 시 올바르게 처리됩니다.
