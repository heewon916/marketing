# API: 임시저장 게시물 캡션 수정

- **Endpoint**: `PATCH /api/v1/contents/{sessionId}/edit`
- **역할**: Redis에 저장된 임시 게시물 캡션을 사용자가 수정한 값으로 덮어씁니다.

## 요청

```json
{
  "caption": "수정된 게시글 캡션입니다."
}
```

## 응답

```json
{
  "session_id": "3f1b7c6e-4e4d-4f6e-9a44-9d7a6f9d2d10",
  "caption": "수정된 게시글 캡션입니다.",
  "updated_at": "2026-05-18T16:30:00+09:00"
}
```

## 현재 처리 흐름

1. `caption`이 null 또는 blank인지 검증합니다.
2. Redis Hash `contents:{sessionId}`가 없으면 업데이트 실패로 처리합니다.
3. `caption`과 `updated_at` 필드를 `HSET`합니다.
4. 수정된 캡션과 서버 기준 갱신 시각을 반환합니다.

## 에러

- `INVALID_REQUEST`: 캡션이 비어 있습니다.
- `CONTENT_NOT_FOUND`: Redis 세션이 없거나 만료되어 업데이트할 수 없습니다.

## 메모

현재 수정 가능한 필드는 `caption`뿐입니다. 이미지 순서나 해시태그 같은 추가 수정은 별도 DTO/Redis 갱신 규칙이 필요합니다.
