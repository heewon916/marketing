# API: 임시저장 게시물 이미지 삭제

- **Endpoint**: `DELETE /api/v1/contents/{sessionId}/images/delete`
- **역할**: Redis 세션에서 특정 `photo:*` 이미지를 삭제합니다.

## 요청

```json
{
  "deleted_image_key": "photo:2"
}
```

`session_id` 필드가 DTO에 남아 있지만 실제 서비스 로직은 path variable의 `sessionId`와 `deleted_image_key`만 사용합니다.

## 응답

```json
{
  "success": true,
  "remaining_images": 2
}
```

## 현재 처리 흐름

1. `deleted_image_key`가 비어 있으면 요청을 거절합니다.
2. Redis Hash `contents:{sessionId}`에서 해당 필드를 `HDEL`합니다.
3. 삭제 후 남은 `photo:*` 값 개수를 조회해 반환합니다.

## 에러

- `INVALID_REQUEST`: `deleted_image_key`가 없거나 비어 있습니다.
- `CONTENT_IMAGE_NOT_FOUND`: 삭제 대상이 `photo:*` 형식이 아니거나 Redis에 존재하지 않습니다.

## 메모

현재 삭제는 Redis 참조만 제거합니다. S3 원본 객체는 삭제하지 않으므로 장기적으로는 별도 정리 작업이 필요합니다.
