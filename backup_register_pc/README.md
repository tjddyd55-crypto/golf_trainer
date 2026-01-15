# 매장 등록 프로그램 백업

이 폴더는 매장 등록 프로그램 관련 파일들의 백업입니다.

## 백업 일시
2026-01-15 (최종 완료 상태)

## 백업된 파일 목록
- `register_pc_gui.py` - 매장 등록 프로그램 (GUI 버전)
- `register_pc.py` - 매장 등록 프로그램 (CLI 버전)
- `build_register_pc_gui.py` - GUI 버전 빌드 스크립트
- `build_register_pc.py` - CLI 버전 빌드 스크립트
- `register_pc_gui.spec` - PyInstaller spec 파일 (GUI)
- `register_pc.spec` - PyInstaller spec 파일 (CLI)
- `register_pc_gui.exe` - 최종 빌드된 실행 파일 (GUI)
- `register_pc.exe` - 최종 빌드된 실행 파일 (CLI)

## 주요 기능
- PC 고유 ID 자동 생성
- 매장 등록 코드 입력
- 서버에 PC 등록 요청
- 등록 상태 확인

## 복원 방법
필요시 이 파일들을 원래 위치로 복사하여 사용할 수 있습니다.

## 사용 방법
1. `register_pc_gui.exe` 또는 `register_pc.exe` 실행
2. 매장 등록 코드 입력
3. PC 등록 요청
4. 서버에서 승인 대기
