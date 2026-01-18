# 리팩터링 2단계 완료 보고서

## 작업 완료 상태
- ✅ **2단계: 죽은 코드/임시 파일 식별** 완료
- ⏳ **실제 파일 삭제/이동** - 사용자 승인 대기 중

---

## 1. 이동한 파일/폴더 목록

### 현재 상태
**아직 파일 이동/삭제를 수행하지 않았습니다.**  
식별만 완료되었으며, 사용자 승인 후 삭제/이동을 진행할 예정입니다.

---

## 2. 수정한 import 파일 목록

### 현재 상태
**아직 import 경로 수정을 수행하지 않았습니다.**  
파일 삭제/이동 후에 필요한 import 경로 수정을 진행할 예정입니다.

---

## 3. 변경된 최상위 폴더 트리 요약

### 현재 상태
**폴더 구조는 아직 변경되지 않았습니다.**  
현재 최상위 폴더 구조는 기존과 동일합니다.

---

## 4. 식별된 파일 목록 (삭제/이동 예정)

### 4.1 사용되지 않는 핵심 파일 (8개)

#### 프로그램 파일 (4개)
1. `shot_collector_gui.py` - main.py에 통합됨
2. `calibrate_regions.py` - CLI 구버전, 사용 안 함
3. `calibrate_regions_overlay.py` - calibrate_regions_gui.py로 통합됨
4. `register_pc.py` - CLI 구버전, GUI 버전만 사용

#### 빌드 스크립트 (4개)
5. `build_shot_collector_gui.py` - 사용 안 함
6. `build_shot_collector.py` - 사용 안 함
7. `build_register_pc.py` - CLI 버전 빌드, 사용 안 함
8. `build_calibrate_regions_overlay.py` - 사용 안 함

### 4.2 임시/테스트/마이그레이션 파일 (약 30개 이상)

#### 생성/마이그레이션 스크립트
- `create_code_final.py`
- `create_code_now.py`
- `create_code_public.py`
- `create_coordinates_table.bat`
- `create_coordinates_table.py`
- `create_coordinates_table.sql`
- `create_registration_code_now.sql`
- `create_test_code.sql`
- `create_test_registration_code.py`
- `create_test_registration_code.sql`
- `database_migration_final.sql`
- `generate_test_code.py`
- `insert_golf_test_code.sql`
- `insert_test_code.py`
- `run_migration_auto.bat`
- `run_migration_direct.py`
- `run_migration_easy.bat`
- `run_migration_final.bat`
- `run_migration_public_url.bat`
- `run_migration_simple.bat`
- `run_migration_simple.py`
- `run_migration_with_url.py`
- `run_migration.bat`
- `run_migration.py`
- `switch_to_railway.py`
- `test_pc_registration.bat`
- `test_railway_connection.py`
- `verify_deployment.py`

#### 기타 임시 파일
- `golf_data.db` - SQLite DB (PostgreSQL 사용 중)
- `debug_ball_speed.png` - 디버그 이미지
- `debug_club_speed.png` - 디버그 이미지
- `GPT키값.txt` - 임시 파일

---

## 5. 다음 단계

### 승인 필요 사항
1. **식별된 파일 삭제 승인** - 위 목록의 파일들을 삭제해도 되는지 확인
2. **파일 이동 계획 승인** - 3단계 이후 폴더 구조 정리 계획 수립 후 이동

### 예상 작업 순서
1. 사용자 승인 후 식별된 파일 삭제
2. 3단계: 공통 유틸 함수 식별
3. 4단계: 폴더 구조 정리 계획 수립
4. 5단계: 파일 이동 및 import 경로 수정
5. 6단계: print → logger 통합
6. 7단계: 최종 검증 및 테스트

---

## 6. 주의사항

### 유지할 파일 (안정성 우선)
- ✅ 모든 문서 파일 (*.md) - 참고용으로 유지
- ✅ `services/` 폴더 내 파일 - 웹 서비스용, 유지
- ✅ `pc_identifier.py` - register_pc_gui.py에서 사용, 유지
- ✅ 백업 폴더 (`backup_*/`) - 유지
- ✅ 빌드 스크립트 (사용 중인 것만) - 유지
  - `build_exe.py`
  - `build_register_pc_gui.py`
  - `build_calibrate_regions_gui.py`

---

## 요약

**현재 상태:**
- ✅ 파일 식별 완료
- ⏳ 파일 삭제/이동 대기 중 (사용자 승인 필요)

**다음 작업:**
- 사용자 승인 후 식별된 파일 삭제
- 3단계로 진행 (공통 유틸 함수 식별)
