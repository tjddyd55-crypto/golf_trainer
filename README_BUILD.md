# Windows 실행 파일 빌드 가이드

## 빌드 방법

### 1. 필요한 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 2. 실행 파일 빌드
```bash
python build_exe.py
```

또는 직접 PyInstaller 사용:
```bash
pyinstaller GolfShotTracker.spec
```

## 빌드 결과

- **실행 파일**: `dist/GolfShotTracker.exe`
- **빌드 파일**: `build/` 폴더 (삭제 가능)

## 배포 방법

골프 컴퓨터에 다음 파일들을 복사:

1. **GolfShotTracker.exe** (dist 폴더에서)
2. **config/** 폴더 전체
3. **regions/** 폴더 전체

```
골프컴퓨터/
├── GolfShotTracker.exe
├── config/
│   ├── criteria.json
│   └── feedback_messages.json
└── regions/
    └── test.json (또는 매장별 json 파일)
```

## 실행 방법

1. 골프 컴퓨터에서 `GolfShotTracker.exe` 더블클릭
2. 콘솔 창이 열리며 실행 상태 확인 가능
3. 골프 화면이 활성화된 상태에서 자동으로 샷 감지

## 주의사항

1. **Tesseract OCR 설치 필요**
   - 골프 컴퓨터에 Tesseract OCR이 설치되어 있어야 합니다
   - 설치 경로: `C:\Program Files\Tesseract-OCR\tesseract.exe`
   - 또는 환경변수 PATH에 추가

2. **Flask 서버 실행 필요**
   - `app.py`가 실행 중이어야 합니다 (포트 5000)
   - 또는 별도 서버에서 실행

3. **폴더 구조**
   - exe 파일과 config, regions 폴더가 같은 위치에 있어야 합니다

4. **콘솔 창**
   - 현재는 콘솔 창이 표시됩니다 (디버깅용)
   - 콘솔 창을 숨기려면 `GolfShotTracker.spec`에서 `console=False`로 변경

## 문제 해결

### 빌드 오류
- PyInstaller 버전 확인: `pip install --upgrade pyinstaller`
- 모든 의존성 설치 확인: `pip install -r requirements.txt`

### 실행 오류
- Tesseract OCR 설치 확인
- config, regions 폴더 존재 확인
- Flask 서버 실행 확인
