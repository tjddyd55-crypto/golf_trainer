# 테스트용 등록 코드

## 등록 코드 생성 방법

### 방법 1: Railway 서버에서 직접 생성 (권장)
Railway PostgreSQL 서버에 접속하여 다음 SQL 실행:

```sql
-- 기존 ACTIVE 코드를 REVOKED로 변경
UPDATE pc_registration_codes 
SET status = 'REVOKED', revoked_at = CURRENT_TIMESTAMP
WHERE status = 'ACTIVE';

-- 새 등록 코드 생성 (테스트용)
INSERT INTO pc_registration_codes (code, status, issued_by, notes)
VALUES ('GOLF-TEST', 'ACTIVE', 'test_admin', '테스트용 등록 코드')
RETURNING code, status, created_at;
```

### 방법 2: 슈퍼 관리자 API 사용
Railway super-admin 서비스가 배포되어 있다면:

```powershell
# PowerShell
$body = @{
    notes = "테스트용"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://golf-super-admin-production.up.railway.app/api/create_registration_code" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
```

### 방법 3: 직접 코드 사용 (임시 테스트)
테스트용 등록 코드 형식: `GOLF-XXXX` (XXXX는 4자리 숫자)

예시:
- `GOLF-1234`
- `GOLF-5678`
- `GOLF-9999`

⚠️ **주의**: 실제 사용하려면 데이터베이스에 등록되어 있어야 합니다.

## 테스트 순서

1. **등록 코드 생성** (위 방법 중 하나 선택)
2. **EXE 파일 실행**
   ```bash
   dist\register_pc.exe
   ```
3. **입력**
   - PC 등록 코드: `GOLF-TEST` (생성한 코드)
   - 매장명: `가자24시`
   - 룸 또는 타석: `1번룸`
4. **결과 확인**
   - 등록 성공 메시지
   - PC 토큰 자동 저장
   - `pc_token.json` 파일 생성

## 현재 상태

✅ EXE 파일 재빌드 완료: `dist/register_pc.exe`

⏳ 등록 코드 생성 필요: Railway 서버에서 생성해야 함
