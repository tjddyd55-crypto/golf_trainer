# PyInstaller Onefile 배포 가이드

## 개요

GolfShotTracker를 PyInstaller onefile 방식으로 빌드하여 단일 exe 파일로 배포할 수 있습니다.
config/와 regions/ 폴더는 자동으로 생성되므로 별도로 복사할 필요가 없습니다.

## 빌드 방법

```bash
python build_exe.py
```

**결과:** `dist/GolfShotTracker.exe` (약 70MB)

## 배포 특징

### ✅ 자동 폴더 생성
- 첫 실행 시 exe와 같은 위치에 `config/`와 `regions/` 폴더가 자동 생성됩니다
- bundled 리소스(`config/criteria.json`, `regions/test.json`)가 자동으로 복사됩니다

### ✅ 경로 처리 통일
- 모든 경로는 `get_base_path()` 기준으로 처리됩니다
- `sys.executable` 기준으로 실행 파일 위치를 결정합니다
- onefile 환경(`sys._MEIPASS`)과 일반 실행 환경을 자동으로 구분합니다

### ✅ 리소스 로드 우선순위
1. **실행 파일 기준 경로** (쓰기 가능)
   - `{exe_dir}/config/criteria.json`
   - `{exe_dir}/regions/test.json`
2. **bundled 리소스** (읽기 전용)
   - `sys._MEIPASS/config/criteria.json`
   - `sys._MEIPASS/regions/test.json`

## 핵심 함수

### 경로 헬퍼 함수

```python
def get_base_path():
    """실행 파일 기준 경로 반환"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    """리소스 파일 경로 반환 (onefile 환경 고려)"""
    # 1. sys._MEIPASS (bundled 리소스) 확인
    # 2. 실행 파일 기준 경로 반환
```

### 자동 폴더 생성

```python
def ensure_config_dirs():
    """config/와 regions/ 폴더가 없으면 생성"""
    # 폴더 생성 + 기본 파일 복사
```

## 배포 절차

1. **빌드**
   ```bash
   python build_exe.py
   ```

2. **배포**
   - `dist/GolfShotTracker.exe` 파일만 복사
   - config/와 regions/ 폴더는 **불필요** (자동 생성됨)

3. **실행**
   - `GolfShotTracker.exe` 실행
   - 첫 실행 시 자동으로 폴더 생성 및 기본 파일 복사

## 테스트 방법

### 1. 빌드 테스트
```bash
cd golf_trainer
python build_exe.py
```

### 2. 실행 테스트
```bash
# 빌드된 exe 실행
dist\GolfShotTracker.exe

# 확인 사항:
# - config/ 폴더 자동 생성 확인
# - regions/ 폴더 자동 생성 확인
# - config/criteria.json 파일 존재 확인
# - regions/test.json 파일 존재 확인
```

### 3. 단독 배포 테스트
```bash
# 임시 폴더 생성
mkdir test_deploy
cd test_deploy

# exe만 복사 (config/, regions/ 제외)
copy ..\dist\GolfShotTracker.exe .

# 실행 (자동 폴더 생성 확인)
.\GolfShotTracker.exe
```

## 주의사항

1. **Tesseract OCR 설치 필요**
   - 골프 컴퓨터에 Tesseract OCR이 설치되어 있어야 합니다

2. **config.json 파일**
   - `config.json` 파일은 자동 생성되지 않습니다
   - 수동으로 생성하거나 서버에서 로드해야 합니다

3. **매장별 좌표 파일**
   - `regions/{store_id}.json` 파일은 서버에서 로드하거나 수동으로 생성해야 합니다
   - 기본 `regions/test.json`은 자동 복사됩니다

## 기술 상세

### 경로 처리 로직

```python
# 실행 파일 기준 경로
base_path = get_base_path()  # sys.executable 기준

# 리소스 로드 우선순위
1. {base_path}/config/criteria.json  # 쓰기 가능
2. {sys._MEIPASS}/config/criteria.json  # bundled (읽기 전용)
```

### 자동 생성 로직

```python
# 첫 실행 시
ensure_config_dirs()
  ├─ config/ 폴더 생성
  ├─ regions/ 폴더 생성
  ├─ config/criteria.json 복사 (bundled → 실행 경로)
  └─ regions/test.json 복사 (bundled → 실행 경로)
```

## 변경 사항 요약

1. ✅ `get_base_path()`: sys.executable 기준 경로 반환
2. ✅ `get_resource_path()`: onefile 환경 고려한 리소스 경로
3. ✅ `ensure_config_dirs()`: config/와 regions/ 자동 생성
4. ✅ `load_json()`: 우선순위 기반 파일 로드
5. ✅ 모든 경로 사용을 헬퍼 함수로 통일

## 빌드 명령어

```bash
pyinstaller --onefile --windowed \
  --name=GolfShotTracker \
  --add-data=config;config \
  --add-data=regions;regions \
  --hidden-import=tkinter \
  --hidden-import=tkinter.ttk \
  --hidden-import=tkinter.messagebox \
  --clean main.py
```

## 문제 해결

### Q: config/ 폴더가 생성되지 않아요
A: `ensure_config_dirs()`가 호출되는지 확인하세요. `main()` 함수 초기화 시 자동 호출됩니다.

### Q: bundled 파일을 찾을 수 없어요
A: `--add-data=config;config --add-data=regions;regions` 옵션이 빌드 명령어에 포함되어 있는지 확인하세요.

### Q: 경로 오류가 발생해요
A: 모든 경로 사용을 `get_base_path()` 또는 `get_resource_path()` 헬퍼 함수로 통일했는지 확인하세요.
