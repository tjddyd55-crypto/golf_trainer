# 좌표 설정 프로그램 백업

이 폴더는 좌표 설정 프로그램 관련 파일들의 백업입니다.

## 백업 일시
2026-01-15 (최종 수정 완료)

## 백업된 파일 목록
- `calibrate_regions_gui.py` - 좌표 설정 프로그램 (최신 오버레이 버전)
- `calibrate_regions_overlay.py` - 오버레이 버전 원본
- `build_calibrate_regions_gui.py` - 빌드 스크립트
- `calibrate_regions_gui.spec` - PyInstaller spec 파일
- `calibrate_regions_gui.exe` - 최종 빌드된 실행 파일

## 주요 기능
- 오버레이 방식 좌표 설정
- 자동 버전 관리 (V1, V2, V3...)
- 브랜드 선택 (골프존, SG골프, 카카오골프, 브라보, 기타)
- 서버 업로드
- 이전/다음 버튼으로 좌표 재설정 가능
- 드래그 시 기존 영역 자동 삭제

## 복원 방법
필요시 이 파일들을 원래 위치로 복사하여 사용할 수 있습니다.

## 최종 수정 사항 (2026-01-15)
1. 이전/다음 버튼 추가 및 하단 배치
2. 브랜드 선택 창 레이아웃 조정 (400x400)
3. 드래그 영역 개선 (기존 영역 자동 삭제)
4. 키보드 단축키 개선 (Left/Right 화살표, Ctrl+BackSpace)
