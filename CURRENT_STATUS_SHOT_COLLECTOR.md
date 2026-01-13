# shot_collector GUI 통합 현재 상태 및 작업 계획

## 현재 상태 (2025-01-XX)

### ✅ 완료된 작업

1. **서버 API 구현** (`services/api/app.py`)
   - ✅ `GET /api/coordinates/{brand}` - 브랜드별 좌표 파일 목록 조회
   - ✅ `GET /api/coordinates/{brand}/{filename}` - 좌표 파일 다운로드
   - ✅ `POST /api/coordinates/upload` - 좌표 파일 업로드

2. **GUI 파일 생성** (`shot_collector_gui.py`)
   - ✅ 브랜드 선택 (콤보박스)
   - ✅ 좌표 파일 선택 (리스트박스)
   - ✅ 시작/종료 버튼
   - ✅ 서버에서 좌표 목록 가져오기
   - ✅ 좌표 파일 다운로드
   - ✅ 트레이 기능 (부분 구현)

3. **main.py 수정**
   - ✅ `run()` 함수에 `temp_regions.json` 로드 로직 추가
   - ✅ GUI에서 다운로드한 좌표 파일 사용 가능

### ⚠️ 현재 문제점

1. **구조적 문제**
   - ❌ GUI가 `subprocess`로 `main.py`를 실행 (복잡함)
   - ❌ 두 개의 exe 파일 필요 (`shot_collector_gui.exe`, `shot_collector.exe`)
   - ❌ 설계 문서(`FINAL_SHOT_COLLECTOR_UX.md`)와 구조 불일치

2. **설계 문서 요구사항**
   - 📋 GUI가 메인 진입점
   - 📋 GUI에서 좌표 선택 후 시작
   - 📋 좌표를 메모리에 고정 (SESSION_COORDS)
   - 📋 샷 수집 루프 시작
   - 📋 GUI 숨김 → 트레이로 이동

### 🔍 현재 구현 방식

```
shot_collector_gui.exe (GUI)
  ↓ 시작 버튼 클릭
  ↓ 좌표 파일 다운로드 → temp_regions.json 저장
  ↓ subprocess로 shot_collector.exe 실행
  ↓ shot_collector.exe가 temp_regions.json 읽어서 실행
  ↓ GUI는 트레이로 이동
```

### 📋 올바른 구조 (설계 문서 기준)

```
shot_collector_gui.exe (GUI - 메인 진입점)
  ↓ 시작 버튼 클릭
  ↓ 좌표 파일 다운로드
  ↓ 좌표를 메모리에 고정 (SESSION_COORDS)
  ↓ main.py의 run() 함수를 import하여 실행 (같은 프로세스)
  ↓ GUI 숨김 → 트레이로 이동
```

## 작업 계획

### 방법 1: GUI를 메인 진입점으로 변경 (권장)

1. **main.py를 모듈화**
   - `run()` 함수를 import 가능하도록 수정
   - 좌표를 함수 파라미터로 전달받도록 수정
   - 또는 전역 변수 `SESSION_COORDS` 사용

2. **shot_collector_gui.py 수정**
   - subprocess 제거
   - `import main` 하여 `main.run(coords)` 호출
   - 트레이 기능을 GUI에 통합

3. **진입점 변경**
   - `shot_collector_gui.py`가 메인 진입점
   - `main.py`는 모듈로 사용
   - exe는 `shot_collector_gui.exe` 하나만 필요

### 방법 2: 현재 구조 개선 (유지)

1. **subprocess 방식 유지**
   - 현재 구조는 유지하되 개선
   - 두 exe 파일 배포

## 권장 사항

**방법 1 (GUI를 메인 진입점)**을 권장합니다.

이유:
- ✅ 설계 문서와 일치
- ✅ 단일 exe 파일 배포
- ✅ 구조 단순
- ✅ 디버깅 용이

## 다음 단계

1. 현재 구조 분석 완료
2. 설계 문서 재확인
3. 방법 1 또는 방법 2 선택
4. 구현
