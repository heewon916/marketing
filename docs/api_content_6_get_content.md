# API: 임시저장 게시물 전체 조회

- **Endpoint**: `GET /api/v1/contents/{sessionId}`
- **역할**: 편집 화면에 필요한 캡션, 이미지, 상태, 인스타그램 프로필 정보를 조회합니다.

## 응답

```json
{
  "session_id": "3f1b7c6e-4e4d-4f6e-9a44-9d7a6f9d2d10",
  "status": "PHOTO_EDITED",
  "caption": "오늘의 시그니처 메뉴를 소개합니다.",
  "images": [
    {
      "id": "photo:1",
      "filtered_url": "/ai-finals/3f1b7c6e-4e4d-4f6e-9a44-9d7a6f9d2d10/final-001.png",
      "display_order": 1
    }
  ],
  "instagram_username": "matketing_store",
  "instagram_profile_image_url": "https://..."
}
```

## 현재 처리 흐름

1. Redis에서 `contents:{sessionId}` 세션을 조회합니다.
2. Security Context의 `AuthUser`에서 인스타그램 사용자명과 프로필 이미지 URL을 읽습니다.
3. Redis의 `photo:*` 필드를 display order 기준 이미지 배열로 매핑합니다.
4. 상태가 비어 있으면 `"draft"`로 정규화합니다.

## 에러

- `CONTENT_NOT_FOUND`: Redis 세션이 없거나 만료되었습니다.
- `UNAUTHORIZED_USER`: 인증 사용자 정보를 찾을 수 없습니다.

## 메모

프론트의 `requestDraftPost()`는 이 응답의 `filtered_url`에 CloudFront 도메인을 붙여 화면에 표시합니다.
