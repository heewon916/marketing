# Weather Caption Context Postman Test Scenario

## 목적

Spring Boot 백엔드의 `POST /api/v1/contents/caption` API가 매장 정보와 사용자 발화를 기반으로 AI 게시글 생성용 참고 JSON을 정상 생성하는지 로컬 Docker 환경에서 검증한다.

검증 대상:
- `store_id`, `utterance`, `owner_persona`, `date`, `weather` 응답 필드
- 기상청 초단기실황/단기예보/특보 API 연동
- 에어코리아 측정소/대기질 API 연동
- Redis 캐시 적용
- store 누락, 좌표 누락, 빈 발화 예외 처리

주의: 이 문서는 `request_id`가 없는 참고 컨텍스트 조회 분기를 주로 다룬다. `request_id`가 있으면 Llama 의도 판별과 FastAPI 캡션 생성 플로우로 넘어간다.

## 1. 환경변수 준비

루트 또는 `be` 기준 `.env`에 아래 값이 있어야 한다.

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=myredispassword

KMA_SERVICE_KEY=공공데이터포털_기상청_서비스키
AIRKOREA_SERVICE_KEY=공공데이터포털_에어코리아_서비스키

KMA_FORECAST_BASE_URL=http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0
KMA_WARNING_BASE_URL=http://apis.data.go.kr/1360000/WthrWrnInfoService
AIRKOREA_AIR_BASE_URL=http://apis.data.go.kr/B552584/ArpltnInforInqireSvc
AIRKOREA_STATION_BASE_URL=http://apis.data.go.kr/B552584/MsrstnInfoInqireSvc

WEATHER_CACHE_TTL_SECONDS=2400
WARNING_CACHE_TTL_SECONDS=600
STATION_CACHE_TTL_SECONDS=86400
```

주의:
- Docker compose 내부에서 백엔드가 Redis 컨테이너를 보려면 Redis host가 `redis`로 전달되어야 한다.
- 공공데이터포털 서비스키는 인코딩/디코딩 이슈가 있을 수 있으므로 실패 시 먼저 키와 승인된 OpenAPI 서비스를 확인한다.

## 2. Docker 기동

루트 디렉터리에서 실행한다.

```powershell
docker compose up -d --build
```

백엔드 로그를 확인한다.

```powershell
docker compose logs -f be
```

확인할 것:
- Spring Boot 정상 기동
- DB 연결 성공
- Redis 연결 성공
- API key empty 로그가 없는지 확인

## 3. 테스트용 Store 확인

`stores` 테이블에 아래 필드가 채워진 row가 필요하다.

- `id`
- `user_id`
- `owner_persona`
- `address`
- `latitude`
- `longitude`

DB에서 확인한다.

```sql
select id, user_id, owner_persona, address, latitude, longitude
from stores
limit 5;
```

권장 테스트 데이터:
- `address`: `서울특별시 중구 세종대로 110`
- `latitude`: `37.5665`
- `longitude`: `126.9780`
- `owner_persona`: `aesthetic`

테스트 데이터가 없으면 현재 schema의 NOT NULL 컬럼을 확인한 뒤 임시 store를 insert한다.

## 4. 정상 요청 테스트

Postman 설정:

- Method: `POST`
- URL: `http://localhost:8080/api/v1/contents/caption`
- Headers:

```http
Content-Type: application/json
Authorization: Bearer <JWT>
```

Body:

```json
{
  "store_id": "실제-stores-id-uuid",
  "utterance": "오늘 가게에 있는 찻잔, 곰돌이 인형, 원목 찬장을 자랑하고 싶어"
}
```

기대 응답:

```json
{
  "store_id": "실제-stores-id-uuid",
  "utterance": "오늘 가게에 있는 찻잔, 곰돌이 인형, 원목 찬장을 자랑하고 싶어",
  "owner_persona": "aesthetic",
  "date": "2026-05-18",
  "weather": {
    "temperature": 18.5,
    "precipitation": 0.0,
    "cloud_cover": "맑음",
    "humidity": 45,
    "wind_speed": 2.5,
    "pm10": 85,
    "pm25": 35,
    "diurnal_range": 12.0,
    "discomfort_index": 63,
    "heavy_rain_warning": null,
    "typhoon_warning": null
  }
}
```

확인할 것:
- `store_id`가 요청한 store UUID와 동일하다.
- `utterance`가 요청 값과 동일하다.
- `owner_persona`가 store 값과 동일하거나, DB 값이 비어 있으면 `aesthetic`이다.
- `date`가 호출일 기준 날짜다.
- `weather` 객체가 존재한다.
- 외부 API 일부 실패 시 `WeatherService.normalizeForAi()`가 기본값으로 보정한다. 특보 필드(`heavy_rain_warning`, `typhoon_warning`)는 없으면 `null`일 수 있다.

## 5. Redis 캐시 검증

같은 store로 같은 시간대에 정상 요청을 한 번 더 호출한다.

기대 결과:
- 응답이 정상 반환된다.
- 두 번째 요청에서는 `weather-context:{storeId}:{yyyyMMddHH}` 캐시 hit로 외부 API 호출이 줄어든다.

Redis key 확인:

```powershell
docker exec -it <redis-container-name> redis-cli -a myredispassword
```

```redis
keys weather-context:*
keys weather-warning:*
keys airkorea-stations:*
ttl weather-context:{storeId}:{yyyyMMddHH}
```

확인할 key:
- `weather-context:{storeId}:{yyyyMMddHH}`
- `weather-warning:{sido}`
- `airkorea-stations:{sido}`

## 6. 좌표 누락 실패 테스트

좌표가 `null`인 store로 요청한다.

Body:

```json
{
  "store_id": "좌표-null-store-uuid",
  "utterance": "테스트"
}
```

기대 결과:
- HTTP 400
- 메시지: `매장 위치 정보가 필요합니다.`

## 7. Store 없음 실패 테스트

존재하지 않는 store UUID로 요청한다.

Body:

```json
{
  "store_id": "00000000-0000-0000-0000-000000000999",
  "utterance": "테스트"
}
```

기대 결과:
- HTTP 400
- 메시지: `매장 정보를 찾을 수 없습니다.`

## 8. 빈 발화 실패 테스트

Body:

```json
{
  "store_id": "실제-store-uuid",
  "utterance": ""
}
```

기대 결과:
- HTTP 400
- 메시지: `캡션 생성을 위한 문장을 입력해 주세요.`

## 9. 로그 확인 포인트

백엔드 로그에서 아래 로그가 반복되는지 확인한다.

```text
weather.kma.ultra-failed
weather.kma.vilage-failed
weather.kma.warning-failed
weather.airkorea.station-failed
weather.airkorea.air-failed
weather.kma.ultra-skipped: KMA_SERVICE_KEY is empty
weather.airkorea.station-skipped: AIRKOREA_SERVICE_KEY is empty
weather.airkorea.air-skipped: AIRKOREA_SERVICE_KEY is empty
```

해석:
- `*-skipped`: 환경변수 서비스키 미주입 가능성이 높다.
- `*-failed: non-success result`: 공공데이터포털 resultCode가 성공이 아니다.
- `request failed`: 네트워크, URL, 서비스키, 승인 상태를 확인한다.
- `response parsing failed`: 응답 구조가 예상과 다르므로 실제 API 응답 body를 확인한다.

## 10. 기존 request_id 기반 캡션 생성 플로우 확인

기존 캡션 생성 흐름도 유지되어야 한다.

Body:

```json
{
  "request_id": "9d5b4b52-78f2-4f7e-8c10-4a04bb5a6b1b",
  "store_id": "실제-store-uuid",
  "utterance": "오늘 가게에 있는 찻잔, 곰돌이 인형, 원목 찬장을 자랑하고 싶어"
}
```

기대 결과:
- Spring이 먼저 Llama 의도 판별을 호출한다.
- `isCreatePost=false`이면 FastAPI를 호출하지 않고 `GENERAL_CHAT` 응답을 반환한다.
- `isCreatePost=true`이면 Redis 멱등성 키를 등록한 뒤 Spring이 weather context를 생성한다.
- 최초 요청이면 FastAPI `/ai/sessions/{session_id}/process-utterance`를 내부 호출한다.
- 응답은 `ChatResponse` 형식이다.
- 같은 `request_id`로 재요청하면 FastAPI를 재호출하지 않고 Redis 멱등성 캐시로 기존 session 결과를 반환한다. 단, 현재 코드는 멱등성 체크보다 Llama 호출이 먼저라 Llama 분류 자체는 재요청 때도 실행된다.
