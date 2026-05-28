# API: 게시물 발행 상태 조회

- **Endpoint**: `GET /api/v1/contents/{sessionId}/publish/status`
- **역할**: Instagram 컨테이너 상태를 조회하고, 완료 시 `media_publish`와 DB 저장까지 수행합니다.

## 응답 예시

```json
{
  "content_id": "123",
  "publish_progress": "completed",
  "instagram_media_id": "17918...",
  "instagram_permalink": "https://www.instagram.com/p/..."
}
```

진행 중이면:

```json
{
  "content_id": null,
  "publish_progress": "uploading",
  "instagram_media_id": null,
  "instagram_permalink": null
}
```

## 현재 처리 흐름

1. Redis 세션을 조회합니다.
2. 이미 `content_id`가 있으면 완료 응답을 반환합니다.
3. `instagram_media_id`는 있지만 DB 저장이 실패했던 상태라면 DB 저장 복구를 시도합니다.
4. `publish_id`가 없으면 `not_started`를 반환합니다.
5. 실패 상태면 `failed`를 반환합니다.
6. `instagram_container_id`가 아직 없으면 현재 `publish_progress`를 반환합니다.
7. Instagram 컨테이너 상태를 조회합니다.
8. `IN_PROGRESS`면 Redis를 `uploading`으로 갱신하고 반환합니다.
9. `FINISHED`가 아니면 실패 처리합니다.
10. `FINISHED`면 Redis lock을 잡고 `media_publish`를 호출합니다.
11. Instagram media id를 Redis에 저장합니다.
12. `Content` 엔티티를 PostgreSQL에 저장하고 Redis를 `completed/PUBLISHED`로 갱신합니다.

## 에러 및 실패 처리

- `CONTENT_NOT_FOUND`: Redis 세션이 없습니다.
- `STORE_NOT_FOUND`: 인증 사용자 기준 매장을 찾을 수 없습니다.
- Instagram API 실패는 Redis `publish_progress=failed`, `status=PUBLISH_FAILED`로 기록하고 응답은 `failed`로 내려갑니다.
- 동시 폴링은 `media_publish_lock:{sessionId}` Redis lock으로 방어합니다.

## 주의점

이 API는 `GET`이지만 상태 변경을 수행합니다. `FINISHED` 상태를 확인하면 Instagram `media_publish`, PostgreSQL 저장, Redis 완료 갱신이 일어납니다. REST 관점에서는 조회와 상태 변경이 섞여 있으므로 장기적으로는 백그라운드 워커 또는 별도 command endpoint로 분리하는 것이 좋습니다.
