# 샷 수집 프로그램 백업 (최신 버전)

## 백업 일자
2026-01-15 (오후 7:11)

## 백업 사유
현재 샷 수집 프로그램이 완벽하게 작동하고 있어, 향후 변경 시 원복을 위해 백업합니다.

## 백업된 파일 목록

1. **main.py**
   - 메인 샷 수집 프로그램
   - GUI 통합, 트레이 상주, OCR 샷 감지 등 모든 핵심 기능 포함
   - 최종 수정 사항:
     - 더블클릭 시 config.json 확인하여 자동 시작
     - config.json 자동 저장 (GUI에서 좌표 선택 시)
     - 트레이 알림 기본값 off
     - 로그 파일 항상 기록 (append 모드)
     - cmd 창 깜빡임 방지
     - 활성 사용자 조회 지연 개선
     - 서버 전송 상세 로그

2. **build_exe.py**
   - PyInstaller를 사용한 exe 빌드 스크립트
   - GolfShotTracker.spec 파일을 사용하여 빌드

3. **GolfShotTracker.spec**
   - PyInstaller spec 파일
   - onefile 배포 설정
   - config, regions 폴더 포함
   - 필수 라이브러리 hiddenimports 설정

4. **pc_identifier.py**
   - PC 고유번호 수집 모듈
   - main.py에서 import하여 사용

5. **setup_autostart.bat**
   - Windows 시작 프로그램 등록 스크립트
   - --autostart 인자 포함하여 바로가기 생성

6. **config.json.example**
   - config.json 설정 예시 파일
   - auto_brand, auto_filename 설정 예시

## 복원 방법

1. 백업 폴더의 파일들을 원래 위치로 복사:
   ```
   main.py → golf_trainer/main.py
   build_exe.py → golf_trainer/build_exe.py
   GolfShotTracker.spec → golf_trainer/GolfShotTracker.spec
   pc_identifier.py → golf_trainer/pc_identifier.py
   setup_autostart.bat → golf_trainer/setup_autostart.bat
   config.json.example → golf_trainer/config.json.example
   ```

2. 빌드 실행:
   ```
   python build_exe.py
   ```

## 현재 상태

- ✅ 샷 감지 및 좌표 읽기 정상 작동
- ✅ 속도 최적화 완료
- ✅ cmd 창 깜빡임 방지
- ✅ 활성 사용자 조회 지연 개선
- ✅ 불필요한 로그/디버그 출력 제거
- ✅ 더블클릭 시 config.json 확인하여 자동 시작
- ✅ config.json 자동 저장 기능
- ✅ 재부팅 시 자동 시작 지원
- ✅ 로그 파일 이어서 작성 (append 모드)

## 주요 기능

### 자동 시작 기능
- 더블클릭 시: config.json에 `auto_brand`, `auto_filename`이 있으면 자동 시작
- 재부팅 시: `setup_autostart.bat`로 등록 시 `--autostart` 인자로 자동 시작
- config.json 자동 저장: GUI에서 좌표 선택 후 시작 시 자동 저장

### 로그 기능
- 모든 샷마다 상세 로그 기록 (runtime.log)
- 재부팅 시에도 로그 이어서 작성 (append 모드)
- 오류 로그 별도 기록 (error.log)

### 백그라운드 실행
- 트레이 알림 기본값 off
- 오류 발생 시 팝업 없음 (GUI가 보이는 상태일 때만 표시)
- 모든 오류는 로그 파일로만 기록

## 주의사항

- 이 백업은 현재 완벽하게 작동하는 버전입니다.
- 향후 수정 시 문제가 발생하면 이 백업으로 원복할 수 있습니다.
- 백업 파일은 수정하지 마세요.
