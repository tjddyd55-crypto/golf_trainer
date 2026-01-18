# Baseline 테스트 가이드

## 목적
리팩터링 전 정상 동작 상태를 확인하고 기준 로그를 확보합니다.

## 테스트 순서

### 1. PC 등록 프로그램 테스트

**실행 방법:**
```bash
python register_pc_gui.py
```

**확인 사항:**
- [ ] 프로그램이 정상적으로 실행되는가?
- [ ] GUI 창이 표시되는가?
- [ ] PC 정보가 정상적으로 수집되는가?
- [ ] 등록 코드 입력 및 등록 요청이 정상 동작하는가?
- [ ] 에러 메시지가 없는가?

**로그 파일 위치:**
- GUI 프로그램이므로 별도 로그 파일 없을 수 있음
- 콘솔 출력 확인 (있는 경우)

**결과 기록:**
- [ ] OK / FAIL
- 에러 내용 (있는 경우): _________________

---

### 2. 좌표 설정(캘리브레이션) 프로그램 테스트

**실행 방법:**
```bash
python calibrate_regions_gui.py
```

**확인 사항:**
- [ ] 프로그램이 정상적으로 실행되는가?
- [ ] GUI 창이 표시되는가?
- [ ] 브랜드 선택이 정상 동작하는가?
- [ ] 화면 캡처가 정상 동작하는가?
- [ ] 좌표 드래그 및 설정이 정상 동작하는가?
- [ ] 좌표 저장 및 서버 업로드가 정상 동작하는가?
- [ ] 에러 메시지가 없는가?

**로그 파일 위치:**
- GUI 프로그램이므로 별도 로그 파일 없을 수 있음
- 콘솔 출력 확인 (있는 경우)

**결과 기록:**
- [ ] OK / FAIL
- 에러 내용 (있는 경우): _________________

---

### 3. 샷 수집 프로그램 테스트

**실행 방법:**
```bash
python main.py
```

**확인 사항:**
- [ ] 프로그램이 정상적으로 실행되는가?
- [ ] GUI 창이 표시되는가? (또는 트레이로 숨김)
- [ ] 좌표 파일 로드가 정상 동작하는가?
- [ ] 샷 감지 로직이 정상 동작하는가?
- [ ] OCR 읽기가 정상 동작하는가?
- [ ] 서버 전송이 정상 동작하는가?
- [ ] 에러 메시지가 없는가?

**로그 파일 위치:**
- `runtime.log` - 런타임 로그
- `error.log` - 에러 로그
- `early_debug.log` - 초기 디버그 로그
- `logs/` 폴더 - 추가 로그 파일들

**결과 기록:**
- [ ] OK / FAIL
- 에러 내용 (있는 경우): _________________

---

## Baseline 로그 저장

**자동 저장 스크립트 실행:**
```bash
create_baseline_logs.bat
```

또는 수동으로:
1. `runtime.log`, `error.log`, `early_debug.log` 파일 확인
2. `baseline_logs/` 폴더에 타임스탬프와 함께 복사

**저장 위치:**
- `baseline_logs/shot_collector_runtime_[timestamp].log`
- `baseline_logs/shot_collector_error_[timestamp].log`
- `baseline_logs/shot_collector_early_debug_[timestamp].log`
- `baseline_logs/shot_collector_logs_[timestamp]/` (폴더)

---

## 테스트 결과 보고

테스트 완료 후 아래 형식으로 보고:

```
### Baseline 테스트 결과

**PC 등록 프로그램:**
- 상태: OK / FAIL
- 에러: (없음 또는 내용)

**좌표 설정 프로그램:**
- 상태: OK / FAIL
- 에러: (없음 또는 내용)

**샷 수집 프로그램:**
- 상태: OK / FAIL
- 에러: (없음 또는 내용)

**Baseline 로그 위치:**
- baseline_logs/[timestamp]/

**확인된 경고/에러:**
- (내용)
```
