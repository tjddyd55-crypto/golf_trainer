# 골프 트레이너 시스템 API 명세서

## 목차
1. [개요](#개요)
2. [기본 정보](#기본-정보)
3. [Health Check API](#health-check-api)
4. [매장 관리 API](#매장-관리-api)
5. [타석 관리 API](#타석-관리-api)
6. [PC 등록 API](#pc-등록-api)
7. [좌표 관리 API](#좌표-관리-api)
8. [샷 데이터 API](#샷-데이터-api)
9. [인증/세션 API](#인증세션-api)

---

## 개요

이 문서는 골프 트레이너 시스템의 서버 API 명세를 정의합니다.  
모든 API는 JSON 형식으로 요청/응답을 처리하며, RESTful 원칙을 따릅니다.

**Base URL**: `https://your-server-url.com` (운영 환경에 따라 변경)

---

## 기본 정보

### 응답 형식

모든 API는 다음 형식의 JSON 응답을 반환합니다:

**성공 응답 (200 OK)**
```json
{
  "success": true,
  "data": { ... }
}
```

**에러 응답 (4xx/5xx)**
```json
{
  "success": false,
  "error": "에러 메시지"
}
```

### HTTP 상태 코드

- `200`: 성공
- `400`: 잘못된 요청 (필수 파라미터 누락, 형식 오류 등)
- `401`: 인증 실패
- `404`: 리소스를 찾을 수 없음
- `410`: 더 이상 지원하지 않는 API (레거시)
- `500`: 서버 내부 오류

---

## Health Check API

### GET /health
### GET /api/health

서버 상태 확인

**Request**
- Method: `GET`
- Parameters: 없음

**Response** (200 OK)
```json
{
  "status": "ok",
  "message": "Server is running"
}
```

---

## 매장 관리 API

### GET /api/get_store

매장 정보 조회 (store_id로 조회)

**Request**
- Method: `GET`
- Query Parameters:
  - `store_id` (required, string): 매장 ID (대문자)

**Response** (200 OK)
```json
{
  "success": true,
  "store_id": "A",
  "store_name": "테스트 매장",
  "business_number": "123-45-67890"
}
```

**Response** (404 Not Found)
```json
{
  "success": false,
  "error": "매장을 찾을 수 없습니다."
}
```

**Response** (400 Bad Request)
```json
{
  "success": false,
  "error": "store_id is required"
}
```

**사용 예시**
```
GET /api/get_store?store_id=A
```

---

## 타석 관리 API

### GET /api/stores/{store_id}/bays

매장 타석 목록 조회 (PC 등록 프로그램에서 사용)

**Request**
- Method: `GET`
- Path Parameters:
  - `store_id` (required, string): 매장 ID

**Response** (200 OK)
```json
{
  "store_id": "A",
  "bays_count": 10,
  "bays": [
    {
      "bay_number": 1,
      "bay_name": "1번룸",
      "assigned": true
    },
    {
      "bay_number": 2,
      "bay_name": null,
      "assigned": false
    }
  ]
}
```

**Response Fields 설명**
- `store_id`: 매장 ID
- `bays_count`: 전체 타석 수
- `bays`: 타석 목록 배열
  - `bay_number`: 타석 번호 (1부터 시작)
  - `bay_name`: 타석 이름 (없으면 null)
  - `assigned`: PC 할당 여부 (true/false)

**사용 예시**
```
GET /api/stores/A/bays
```

### GET /api/stores/{store_id}/bays/{bay_number}/coordinates

타석별 등록된 좌표 정보 조회 (TODO: 구현 예정)

**Request**
- Method: `GET`
- Path Parameters:
  - `store_id` (required, string): 매장 ID
  - `bay_number` (required, integer): 타석 번호

**Response** (200 OK)
```json
{
  "success": true,
  "coordinate": {
    "brand": "SGGOLF",
    "resolution": "1920x1080",
    "version": 1,
    "coordinate_id": "SGGOLF-1920x1080-v1"
  }
}
```

**Response** (404 Not Found - 좌표 미지정)
```json
{
  "success": false,
  "error": "좌표가 지정되지 않았습니다."
}
```

**사용 예시**
```
GET /api/stores/A/bays/1/coordinates
```

---

## PC 등록 API

### POST /api/pcs/register

PC 등록 (bay_number 기반, 신규 방식)

**Request**
- Method: `POST`
- Content-Type: `application/json`
- Body:
```json
{
  "store_id": "A",
  "pc_unique_id": "PC-UUID-12345",
  "bay_number": 3,
  "bay_name": "3번룸"
}
```

**Request Fields 설명**
- `store_id` (required, string): 매장 ID
- `pc_unique_id` (required, string): PC 고유 ID (MAC 주소 + UUID 조합)
- `bay_number` (required, integer): 타석 번호
- `bay_name` (optional, string): 타석 이름

**Response** (200 OK)
```json
{
  "success": true,
  "message": "PC 등록이 완료되었습니다.",
  "bay_id": 123,
  "bay_number": 3
}
```

**Response** (400 Bad Request)
```json
{
  "success": false,
  "error": "이미 다른 타석에 등록된 PC입니다."
}
```

**Response** (404 Not Found)
```json
{
  "success": false,
  "error": "매장 또는 타석을 찾을 수 없습니다."
}
```

**사용 예시**
```bash
curl -X POST https://your-server-url.com/api/pcs/register \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "A",
    "pc_unique_id": "PC-UUID-12345",
    "bay_number": 3,
    "bay_name": "3번룸"
  }'
```

### POST /api/register_pc
### POST /pc/register

레거시 PC 등록 API (더 이상 사용 불가)

**Response** (410 Gone)
```json
{
  "ok": false,
  "error": "구버전 등록프로그램입니다. 최신 버전을 사용하세요."
}
```

---

## 좌표 관리 API

### GET /api/coordinates
### GET /api/coordinates?brand={brand}
### GET /api/coordinates/{brand}

브랜드별 좌표 파일 목록 조회

**Request**
- Method: `GET`
- Query Parameters (권장):
  - `brand` (required, string): 브랜드명 (예: SGGOLF, GOLFZON)
- Path Parameters (대안):
  - `brand` (required, string): 브랜드명

**참고**: 쿼리 파라미터가 경로 파라미터보다 우선순위가 높습니다.

**Response** (200 OK)
```json
{
  "success": true,
  "files": [
    {
      "filename": "coordinates_v1.json",
      "brand": "SGGOLF",
      "resolution": "1920x1080",
      "version": 1,
      "created_at": "2024-01-01T00:00:00"
    },
    {
      "filename": "coordinates_v2.json",
      "brand": "SGGOLF",
      "resolution": "1920x1080",
      "version": 2,
      "created_at": "2024-01-02T00:00:00"
    }
  ]
}
```

**Response Fields 설명**
- `success`: 요청 성공 여부
- `files`: 좌표 파일 목록 배열
  - `filename`: 파일명
  - `brand`: 브랜드명
  - `resolution`: 해상도 (예: "1920x1080")
  - `version`: 버전 번호
  - `created_at`: 생성 일시 (ISO 8601 형식)

**Response** (400 Bad Request)
```json
{
  "success": false,
  "error": "brand parameter is required"
}
```

**사용 예시**
```
GET /api/coordinates?brand=SGGOLF
GET /api/coordinates/GOLFZON
```

### GET /api/coordinates/{brand}/{filename}

좌표 파일 다운로드

**Request**
- Method: `GET`
- Path Parameters:
  - `brand` (required, string): 브랜드명
  - `filename` (required, string): 파일명

**Response** (200 OK)
```json
{
  "success": true,
  "data": {
    "regions": [
      {
        "name": "region1",
        "coordinates": [ ... ]
      }
    ]
  }
}
```

**Response** (404 Not Found)
```json
{
  "success": false,
  "error": "File not found"
}
```

**사용 예시**
```
GET /api/coordinates/SGGOLF/coordinates_v1.json
```

### POST /api/coordinates/assign

타석에 좌표 할당 (TODO: 구현 예정)

**Request**
- Method: `POST`
- Content-Type: `application/json`
- Body:
```json
{
  "store_id": "A",
  "bay_number": 2,
  "brand": "GOLFZON",
  "coordinate_id": "GOLFZON-1920x1080-v1"
}
```

**Request Fields 설명**
- `store_id` (required, string): 매장 ID
- `bay_number` (required, integer): 타석 번호
- `brand` (required, string): 브랜드명
- `coordinate_id` (required, string): 좌표 ID (형식: "{brand}-{resolution}-v{version}")

**Response** (200 OK)
```json
{
  "success": true,
  "message": "좌표가 할당되었습니다."
}
```

**Response** (400 Bad Request)
```json
{
  "success": false,
  "error": "잘못된 요청입니다."
}
```

**Response** (404 Not Found)
```json
{
  "success": false,
  "error": "매장, 타석 또는 좌표를 찾을 수 없습니다."
}
```

### POST /api/coordinates/upload

좌표 파일 업로드 (슈퍼 관리자 전용)

**Request**
- Method: `POST`
- Headers:
  - `Authorization: Basic {base64(username:password)}`
- Content-Type: `application/json`
- Body:
```json
{
  "brand": "SGGOLF",
  "resolution": "1920x1080",
  "regions": [
    {
      "name": "region1",
      "coordinates": [ ... ]
    }
  ]
}
```

**Response** (200 OK)
```json
{
  "success": true,
  "message": "좌표 파일이 업로드되었습니다.",
  "filename": "coordinates_v1.json"
}
```

**Response** (401 Unauthorized)
```json
{
  "success": false,
  "error": "Unauthorized"
}
```

---

## 샷 데이터 API

### POST /api/save_shot

샷 데이터 저장

**Request**
- Method: `POST`
- Headers:
  - `Authorization: Bearer {pc_token}` (optional)
- Content-Type: `application/json`
- Body:
```json
{
  "pc_unique_id": "PC-UUID-12345",
  "shot_data": {
    "ball_speed": 150,
    "club_speed": 120,
    ...
  }
}
```

**Response** (200 OK)
```json
{
  "status": "ok"
}
```

**Response** (400 Bad Request)
```json
{
  "status": "error",
  "message": "데이터가 없습니다"
}
```

---

## 인증/세션 API

### GET /api/active_user

활성 사용자 조회

**Request**
- Method: `GET`
- Headers:
  - `Authorization: Bearer {pc_token}` (optional)

**Response** (200 OK)
```json
{
  "success": true,
  "pc_unique_id": "PC-UUID-12345",
  "store_id": "A",
  "bay_number": 3
}
```

### POST /api/verify_pc

PC 토큰 검증

**Request**
- Method: `POST`
- Headers:
  - `Authorization: Bearer {pc_token}` (optional)
- Content-Type: `application/json`
- Body (Authorization 헤더가 없을 경우):
```json
{
  "pc_token": "token-string"
}
```

**Response** (200 OK)
```json
{
  "success": true,
  "pc_unique_id": "PC-UUID-12345",
  "store_id": "A",
  "bay_id": "3",
  "status": "active"
}
```

**Response** (401 Unauthorized)
```json
{
  "success": false,
  "error": "PC token is required"
}
```

### POST /api/clear_session

세션 초기화

**Request**
- Method: `POST`

**Response** (200 OK)
```json
{
  "success": true,
  "message": "세션이 초기화되었습니다."
}
```

---

## 주의사항

### 좌표 ID 형식

좌표 ID는 다음 형식으로 조합됩니다:
- `resolution`이 있는 경우: `{brand}-{resolution}-v{version}`
- `resolution`이 없는 경우: `{brand}-{filename}-v{version}`

**예시**:
- `SGGOLF-1920x1080-v1`
- `GOLFZON-1920x1080-v2`
- `SGGOLF-coordinates_v1.json-v1` (resolution 없을 경우)

### 브랜드 목록

현재 서버에는 브랜드 목록을 조회하는 전용 API가 없습니다.  
클라이언트는 하드코딩된 브랜드 목록을 사용하거나, 향후 추가될 API를 사용할 수 있습니다:

**예상 API** (구현 예정):
```
GET /api/coordinates/brands
```

**Fallback 브랜드 목록**:
- `SGGOLF`
- `GOLFZON`
- `GOLFZONNEW`
- `GOLFZONPREMIUM`

### 타석 번호 형식

타석 번호는 **1부터 시작**하는 정수입니다.

---

## 에러 처리

모든 API는 일관된 에러 응답 형식을 사용합니다:

```json
{
  "success": false,
  "error": "에러 메시지"
}
```

**주요 에러 코드**:
- `400`: 필수 파라미터 누락, 잘못된 데이터 형식
- `401`: 인증 실패 (토큰 없음, 잘못된 토큰)
- `404`: 리소스를 찾을 수 없음 (매장, 타석, 파일 등)
- `500`: 서버 내부 오류

---

## 버전 정보

**API 버전**: v1.0  
**문서 최종 업데이트**: 2024-01-XX  
**서버 코드 위치**: `services/api/app.py`

---

## TODO (구현 예정)

다음 API들은 현재 클라이언트에서 사용하지만 서버에 아직 구현되지 않았습니다:

1. **GET /api/stores/{store_id}/bays/{bay_number}/coordinates**
   - 타석별 등록된 좌표 정보 조회

2. **POST /api/coordinates/assign**
   - 타석에 좌표 할당

3. **GET /api/coordinates/brands**
   - 브랜드 목록 조회

이러한 API들을 사용하는 클라이언트는 현재 404 또는 에러 응답을 받게 됩니다.
