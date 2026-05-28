# `/api/v1/contents/caption` Llama 의도 판별 트러블슈팅

작성일: 2026-05-17  
최종 갱신: 2026-05-18  
대상: Spring Backend `/api/v1/contents/caption`, `LlamaIntentClient`, FastAPI `process-utterance`

## 현재 코드 기준 흐름

`request_id`가 있는 `/caption` 요청만 Llama 의도 판별을 수행한다.

```text
POST /api/v1/contents/caption
  request_id 없음
    -> Llama 호출 없음
    -> FastAPI 호출 없음
    -> store/persona/date/weather 참고 JSON 반환

  request_id 있음
    -> utterance/request_id 검증
    -> LlamaIntentClient.classify(utterance)
      isCreatePost=false
        -> GENERAL_CHAT ChatResponse 반환
      isCreatePost=true
        -> Redis idempotency key SET NX EX
        -> 중복 request_id면 Redis 기존 결과 반환
        -> 최초 request_id면 store/weather context 생성
        -> FastAPI POST /ai/sessions/{sessionId}/process-utterance
        -> Redis contents:{sessionId} 업데이트
        -> ChatResponse 반환
```

주의: 현재는 Redis 멱등성 체크보다 Llama 호출이 먼저다. 같은 `request_id`를 재요청해도 Llama 분류는 다시 실행된다.

## Llama 호출 방식

현재 `LlamaIntentClient`는 Spring AI `OllamaChatModel` 경로가 아니라 llama.cpp/OpenAI-compatible 경로를 직접 호출한다.

```text
POST {OLLAMA_BASE_URL}/v1/chat/completions
```

설정 주입:

```java
@Value("${spring.ai.ollama.base-url:${OLLAMA_BASE_URL:}}") String baseUrl
@Value("${spring.ai.ollama.chat.model:${OLLAMA_MODEL:local-model}}") String model
@Value("${llama.intent.timeout-seconds:120}") long timeoutSeconds
```

요청 주요 옵션:

```json
{
  "response_format": { "type": "json_object" },
  "stream": false,
  "max_tokens": 96,
  "temperature": 0.0
}
```

기대 응답:

```json
{
  "isCreatePost": false,
  "reply": "오늘 많이 힘드셨군요. 잠깐 쉬어가셔도 괜찮아요."
}
```

`is_create_post`도 `@JsonAlias`로 받을 수 있다.

## 응답별 처리

### `isCreatePost=false`

Spring은 FastAPI를 호출하지 않고 바로 반환한다.

```json
{
  "session_id": null,
  "status": "GENERAL_CHAT",
  "guide_text": "",
  "caption": "Llama reply 또는 fallback 문구"
}
```

일반 대화 답변은 현재 `caption` 필드에 실린다.

### `isCreatePost=false`, `reply` 비어 있음

JSON 파싱은 성공했지만 Llama가 지시를 일부 어긴 상태다. 고정 문구로 보정한다.

```text
괜찮아요. 잠시 숨 고르고 천천히 이야기해 주세요.
```

### Llama 응답 비어 있음 또는 JSON 아님

키워드 기반 fallback을 사용한다.

게시글 관련 키워드:

```text
인스타, instagram, 게시물, 피드, 캡션, caption, 릴스, reels,
홍보, 포스팅, post, 올려, 올릴, 만들, 작성, 소개
```

키워드가 있으면:

```json
{ "isCreatePost": true, "reply": "" }
```

키워드가 없으면:

```json
{
  "isCreatePost": false,
  "reply": "괜찮아요. 오늘 많이 지치셨다면 잠깐 쉬어가셔도 좋아요."
}
```

### `isCreatePost=true`

최초 요청이면 Spring이 새 `sessionId`를 만들고 FastAPI를 호출한다.

```text
POST /ai/sessions/{sessionId}/process-utterance
```

FastAPI 응답:

```json
{
  "session_id": "{sessionId}",
  "status": "TEXT_GENERATED",
  "guide_text": "메뉴가 잘 보이도록 가까이 찍어주세요.",
  "caption": "오늘의 시그니처 메뉴를 소개합니다."
}
```

Spring은 `status`를 `ContentStatus`로 정규화하고 `guide_text`, `caption`을 Redis에 저장한 뒤 프론트에 반환한다.

## 자주 본 문제

### 1. `/api/chat` 404

증상:

```text
POST /api/chat 404 Not Found
```

원인:

```text
Spring AI Ollama client는 /api/chat을 호출한다.
llama.cpp server는 /v1/chat/completions를 제공한다.
```

현재 해결 상태:

```text
LlamaIntentClient가 RestClient로 /v1/chat/completions를 직접 호출한다.
```

확인 명령:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "$env:OLLAMA_BASE_URL/v1/chat/completions" `
  -ContentType "application/json" `
  -TimeoutSec 120 `
  -Body '{
    "model": "llama3.2",
    "messages": [
      {"role":"user","content":"JSON only: {\"isCreatePost\":false,\"reply\":\"안녕하세요\"}"}
    ],
    "response_format": {"type":"json_object"},
    "stream": false,
    "max_tokens": 64,
    "temperature": 0.0
  }'
```

### 2. Llama 서버 timeout

증상:

```text
llama.cpp server가 should_stop 또는 timeout으로 completion을 중단
Spring 응답은 AI_SERVER_FAILED
```

확인할 것:

- `llama.intent.timeout-seconds` 또는 `LLAMA_INTENT_TIMEOUT_SECONDS`
- llama.cpp server의 `--timeout`
- 모델 크기, GPU layer, 토큰 생성 속도

의도 판별은 짧은 JSON만 필요하므로 `max_tokens=96` 이상을 크게 늘릴 이유가 없다.

### 3. JSON이 아닌 문장 응답

증상:

```json
{
  "code": "AI_SERVER_FAILED",
  "message": "캡션 생성에 실패했습니다. 잠시 후 다시 시도해 주세요."
}
```

현재 코드에서는 JSON 객체를 못 찾으면 즉시 실패하지 않고 fallback을 탄다. 그래도 `AI_SERVER_FAILED`가 난다면 아래를 확인한다.

- Llama HTTP 호출 자체 실패
- 응답 DTO 구조가 OpenAI-compatible이 아님
- JSON처럼 보이지만 필드 타입이 파싱 불가능함
- base URL이 잘못되어 HTML/ngrok 에러 페이지가 반환됨

### 4. true 분기에서 FastAPI 실패

`isCreatePost=true`는 Llama 이후 FastAPI까지 정상이어야 성공한다.

필수 조건:

```text
AI_SERVER_BASE_URL이 FastAPI를 정확히 가리킴
FastAPI 컨테이너가 떠 있음
FastAPI가 Redis/Postgres/S3 설정에 접근 가능
KEYWORD_MODEL_BASE_URL / CAPTION_MODEL_BASE_URL 접근 가능
store 좌표가 존재함
weather context 생성 가능
```

Spring 로그 포인트:

```text
content.ai.process-utterance.failed
content.ai.process-utterance.invalid-response
```

FastAPI 로그 포인트:

```text
process-utterance request received.
process-utterance completed successfully.
```

### 5. 프론트 콘솔에 Llama 응답처럼 보이는 값이 찍힘

현재 Spring 코드에서 성공한 Llama 응답을 콘솔에 출력하지 않는다. 브라우저 콘솔에 찍히는 값은 보통 프론트의 `/caption` 최종 응답 로그다.

프론트 로그 위치:

```text
fe/src/features/home/api/HomeApi.js
console.log("requestId", requestId)
console.log(data)
```

정상 게시글 생성 응답은 아래 형태여야 한다.

```json
{
  "session_id": "...",
  "status": "TEXT_GENERATED",
  "guide_text": "...",
  "caption": "..."
}
```

브라우저 콘솔에 `isCreatePost`가 그대로 보이면 확인할 것:

- 프론트 API base URL이 Spring이 아닌 Llama 서버를 가리키는지
- 실행 중인 백엔드가 현재 코드가 맞는지
- 프록시가 `/api/v1/contents/caption`을 다른 곳으로 라우팅하는지

## Postman 테스트

### GENERAL_CHAT 분기

```http
POST http://localhost:8080/api/v1/contents/caption
Authorization: Bearer <JWT>
Content-Type: application/json
```

```json
{
  "request_id": "11111111-1111-1111-1111-111111111111",
  "store_id": "663c31d7-87c6-4b83-bc0b-756e84a7a3a7",
  "utterance": "오늘 너무 힘들다"
}
```

기대:

```json
{
  "session_id": null,
  "status": "GENERAL_CHAT",
  "guide_text": "",
  "caption": "..."
}
```

### 게시글 생성 분기

```json
{
  "request_id": "22222222-2222-2222-2222-222222222222",
  "store_id": "663c31d7-87c6-4b83-bc0b-756e84a7a3a7",
  "utterance": "오늘 비 오는 날에 어울리는 밤호박치즈케이크 인스타 게시물 캡션 만들어줘"
}
```

기대 흐름:

```text
Llama isCreatePost=true
Redis idempotency key 저장
FastAPI /ai/sessions/{sessionId}/process-utterance 호출
TEXT_GENERATED 응답
```

## 체크리스트

- [ ] `OLLAMA_BASE_URL`이 `/v1/chat/completions`를 제공하는 서버인지 확인
- [ ] `OLLAMA_MODEL`이 서버에서 허용되는 모델명인지 확인
- [ ] Llama timeout이 모델 속도에 비해 너무 짧지 않은지 확인
- [ ] `request_id`가 UUID 형식인지 확인
- [ ] `request_id` 없는 요청은 Llama/FastAPI를 호출하지 않는다는 점 확인
- [ ] true 분기는 `AI_SERVER_BASE_URL`과 FastAPI 상태 확인
- [ ] FastAPI의 Redis/Postgres/S3/모델 서버 연결 확인
- [ ] 프론트 콘솔 로그가 Llama 직접 응답인지 Spring 최종 응답인지 구분
