# API: 게시물 캡션 생성 및 참고 컨텍스트 조회

- **Endpoint**: `POST /api/v1/contents/caption`
- **역할**: `request_id` 유무에 따라 게시물 생성 참고 컨텍스트를 반환하거나, Llama 의도 판별 후 FastAPI 캡션 생성을 실행합니다.

## 요청

```json
{
  "request_id": "9d5b4b52-78f2-4f7e-8c10-4a04bb5a6b1b",
  "store_id": "663c31d7-87c6-4b83-bc0b-756e84a7a3a7",
  "utterance": "오늘 비 오는 날에 어울리는 밤호박치즈케이크 인스타 게시물 캡션 만들어줘"
}
```

| 필드 | 필수 | 설명 |
|---|---:|---|
| `request_id` | 선택 | 있으면 캡션 생성 플로우를 실행합니다. UUID 형식이어야 합니다. 없으면 참고 컨텍스트만 반환합니다. |
| `store_id` | 선택 | 없으면 인증 사용자 기준 첫 매장을 조회합니다. |
| `utterance` | 예 | 사용자 발화입니다. |

## 분기 A: `request_id` 없음

FastAPI와 Llama를 호출하지 않습니다. 매장, 페르소나, 날짜, 날씨 컨텍스트만 반환합니다.

```json
{
  "store_id": "663c31d7-87c6-4b83-bc0b-756e84a7a3a7",
  "utterance": "오늘 신메뉴를 소개하고 싶어",
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

## 분기 B: `request_id` 있음

현재 코드의 순서는 아래와 같습니다.

1. `utterance`와 `request_id`를 검증합니다.
2. `LlamaIntentClient.classify(utterance)`로 게시글 작성 의도를 판별합니다.
3. `isCreatePost=false`면 FastAPI를 호출하지 않고 `GENERAL_CHAT`을 반환합니다.
4. `isCreatePost=true`면 새 `sessionId`를 만들고 Redis 멱등성 키를 `SET NX EX`로 등록합니다.
5. 중복 `request_id`면 FastAPI를 재호출하지 않고 Redis의 기존 결과를 반환합니다.
6. 최초 요청이면 매장/날씨 컨텍스트를 만든 뒤 FastAPI `POST /ai/sessions/{sessionId}/process-utterance`를 호출합니다.
7. FastAPI 응답의 `status`, `guide_text`, `caption`을 Redis에 저장하고 프론트에 반환합니다.

### 일반 대화 응답

```json
{
  "session_id": null,
  "status": "GENERAL_CHAT",
  "guide_text": "",
  "caption": "괜찮아요. 잠시 숨 고르고 천천히 이야기해 주세요."
}
```

`caption`에는 Llama가 만든 일반 대화 답변이 들어갑니다. Llama가 `isCreatePost=false`인데 `reply`를 비워서 주면 고정 문구로 보정합니다.

### 게시물 생성 응답

```json
{
  "session_id": "3f1b7c6e-4e4d-4f6e-9a44-9d7a6f9d2d10",
  "status": "TEXT_GENERATED",
  "guide_text": "메뉴가 잘 보이도록 가까이 찍어주세요.",
  "caption": "비 오는 날엔 달콤한 밤호박치즈케이크 한 조각 어떠세요?"
}
```

`guide_text`와 `caption`은 FastAPI 응답값입니다. `status`는 Spring에서 `ContentStatus` enum으로 정규화합니다.

## Llama 의도 판별

- 호출 경로: `OLLAMA_BASE_URL` 또는 `spring.ai.ollama.base-url` + `/v1/chat/completions`
- 응답 형식: OpenAI-compatible chat completion
- 요청 옵션: `response_format={"type":"json_object"}`, `stream=false`, `max_tokens=96`, `temperature=0.0`
- 기대 JSON: `{"isCreatePost":true,"reply":""}` 또는 `{"isCreatePost":false,"reply":"..."}`

Llama 응답이 비었거나 JSON이 아니면 키워드 fallback을 사용합니다. 게시글 관련 키워드가 있으면 `true`, 없으면 `false`로 처리합니다.

## 에러

- `EMPTY_UTTERANCE`: 발화가 비어 있습니다.
- `INVALID_REQUEST`: `request_id`가 없거나 UUID 형식이 아닙니다. 단, `request_id` 없는 컨텍스트 조회 분기는 허용됩니다.
- `STORE_NOT_FOUND`: 매장을 찾을 수 없습니다.
- `STORE_COORDINATE_REQUIRED`: 날씨 컨텍스트에 필요한 매장 좌표가 없습니다.
- `AI_SERVER_FAILED`: Llama 또는 FastAPI 호출 실패, FastAPI 응답 필수 필드 누락, 알 수 없는 상태값입니다.

## 현재 주의점

- 멱등성 체크보다 Llama 호출이 먼저 실행됩니다. 같은 `request_id` 재요청이어도 Llama는 다시 호출됩니다.
- `request_id`가 없으면 게시글 생성 의도 판별도 하지 않습니다.
- `GENERAL_CHAT`도 `ChatResponse` 형식을 사용하므로 일반 대화 답변은 `caption` 필드에 들어갑니다.
