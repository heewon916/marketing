# API: 임시저장 게시물 이미지 조회

- **Endpoint**: `GET /api/v1/contents/{sessionId}/images`
- **역할**: Redis에 저장된 최종 편집 이미지 목록을 조회합니다.

## 응답

```json
{
  "session_id": "3f1b7c6e-4e4d-4f6e-9a44-9d7a6f9d2d10",
  "image_url": [
    {
      "image_key": "photo:1",
      "image_url": "/ai-finals/3f1b7c6e-4e4d-4f6e-9a44-9d7a6f9d2d10/final-001.png"
    }
  ]
}
```

## 현재 처리 흐름

1. `sessionId`로 Redis Hash `contents:{sessionId}`의 `photo:*` 필드를 조회합니다.
2. 필드명은 `image_key`, 값은 `image_url`로 매핑합니다.
3. 세션 존재 여부를 별도로 검증하지 않고, 이미지가 없으면 빈 배열을 반환합니다.

## 에러

현재 서비스 로직에서는 세션이 없다는 이유만으로 예외를 던지지 않습니다. UUID path variable 파싱 실패는 Spring MVC 레벨에서 처리됩니다.

## 메모

세션 없음과 이미지 없음은 의미가 다르지만 현재 API는 둘을 구분하지 않습니다. 프론트는 빈 목록을 정상 빈 상태로 처리해야 합니다.
