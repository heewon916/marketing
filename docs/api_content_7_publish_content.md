# API: 게시물 발행 시작

- **Endpoint**: `POST /api/v1/contents/{sessionId}/publish`
- **역할**: Redis 임시 게시물을 Instagram Graph API 컨테이너 생성 단계까지 진행하고 발행 상태를 `queued/uploading`으로 전환합니다.

## 응답

```json
{
  "content_id": "f1b7c6e4-...",
  "publish_progress": "queued",
  "message": "발행이 시작되었습니다"
}
```

이미 발행 완료된 세션이면 기존 `content_id`와 permalink 메시지를 반환합니다. 이미 컨테이너가 생성되어 진행 중이면 `"발행이 진행 중입니다"`를 반환합니다.

## 현재 처리 흐름

1. Redis 세션을 조회합니다.
2. 이미 `content_id`가 있으면 완료 응답을 반환합니다.
3. 이미 `publish_id`와 `instagram_container_id`가 있으면 진행 중 응답을 반환합니다.
4. 캡션이 비어 있으면 요청을 거절합니다.
5. `photo:*` 이미지를 CloudFront 공개 URL로 변환합니다.
6. 이미지가 없으면 발행할 수 없습니다. 영상만 있는 세션도 현재는 거절합니다.
7. 이미지가 10장을 초과하면 거절합니다.
8. 인증 사용자와 매장을 조회하고 Instagram access token을 검증합니다.
9. Redis에 `publish_id`, `publish_progress=queued`, `status=PUBLISHING`을 저장합니다.
10. Instagram 이미지 또는 캐러셀 컨테이너를 생성하고 `instagram_container_id`, `publish_progress=uploading`을 저장합니다.

## 에러

- `CONTENT_NOT_FOUND`: Redis 세션이 없습니다.
- `INVALID_REQUEST`: 캡션 없음, 영상만 있음, 이미지 10장 초과 등.
- `INSTAGRAM_MEDIA_REQUIRED`: 이미지와 영상이 모두 없습니다.
- `STORE_NOT_FOUND`: 인증 사용자 기준 매장을 찾을 수 없습니다.
- `INSTAGRAM_TOKEN_REQUIRED`: Instagram access token이 없습니다.
- `INSTAGRAM_PUBLISH_FAILED`: Instagram 컨테이너 생성에 실패했습니다.

## 현재 제한

Reels 발행은 비활성화되어 있습니다. Redis 세션에 영상 key가 있어도 이미지가 있으면 영상은 발행에서 무시되고, 이미지 기반 게시물만 발행합니다.
