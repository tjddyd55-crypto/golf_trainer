# PC 등록 프로그램 테스트 가이드

## 현재 PC 정보
- **PC 고유번호**: C479A32F7BB72C64028D2B90638172CD
- **MAC 주소**: bc:f3:cd:37:dc:71
- **PC UUID**: 95a4a5fe-69e3-4816-bfd0-bcda96e372b8 (machine_guid)
- **호스트명**: DESKTOP-VG5J7U7
- **플랫폼**: Windows

## 테스트 단계

### 1. Railway API 서비스 URL 확인
Railway 대시보드에서 `golf-api` 서비스의 URL을 확인하세요.
- 예: `https://golf-api-production.up.railway.app`

### 2. PC 등록 프로그램 실행
```bash
python register_pc.py
```

### 3. 등록 정보 입력
프로그램 실행 시 다음 정보를 입력하세요:
- **매장명**: 테스트용 매장명 (예: "테스트매장")
- **타석번호**: 테스트용 타석번호 (예: "테스트타석1")
- **PC 이름**: 테스트용 PC 이름 (예: "테스트PC")
- **서버 URL**: Railway API 서비스 URL (예: `https://golf-api-production.up.railway.app`)

### 4. 등록 확인
등록 성공 시:
- "PC 등록 성공!" 메시지 표시
- PC 코드 표시
- "승인 대기 중" 상태 안내

### 5. 관리자 승인
슈퍼 관리자 대시보드에서:
1. `/pcs` 경로로 접속
2. 등록된 PC 목록 확인
3. 승인 버튼 클릭
4. `store_id`, `bay_id` 지정 (예: "gaja", "01")
5. 승인 완료 → 토큰 자동 발급

### 6. 토큰 저장 확인
승인 후 `pc_token.json` 파일이 생성되는지 확인:
```bash
type pc_token.json
```

## 문제 해결

### 서버 연결 실패
- Railway API 서비스가 정상 실행 중인지 확인
- 서버 URL이 올바른지 확인
- 방화벽/네트워크 설정 확인

### PC UUID 수집 실패
- Windows 관리자 권한으로 실행
- `wmic` 명령어 실행 권한 확인

### 등록 실패
- 서버 로그 확인 (Railway 대시보드)
- 네트워크 연결 확인
- 필수 정보 (MAC, UUID) 수집 확인

## 다음 단계

1. ✅ PC 정보 수집 테스트 완료
2. ⏳ PC 등록 프로그램 실행 (수동 입력 필요)
3. ⏳ 서버 등록 확인
4. ⏳ 관리자 승인 테스트
5. ⏳ 토큰 저장 확인
6. ⏳ main.py 인증 테스트
