# API: 비디오 업로드 및 AI 프레임 추출

- **Endpoint**: `POST /api/v1/contents/{sessionId}/video`
- **Content-Type**: `multipart/form-data`
- **역할**: 촬영 영상을 S3에 저장하고, FastAPI 프레임 추출 및 최종 이미지 보정 파이프라인을 동기 호출합니다.

## 요청

| 필드 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| `video_file` | File | 예 | 프론트 `CameraStep`이 생성한 녹화 파일입니다. 현재 프론트는 webm 계열만 생성합니다. |
| `store_id` | Query | 아니오 | 현재 `processVideo`에서는 전달만 받고 별도 조회에 사용하지 않습니다. |

프론트 현재 생성 MIME 후보:

```text
video/webm;codecs=vp9,opus
video/webm;codecs=vp8,opus
video/webm
```

파일명도 `recorded-{timestamp}.webm`으로 생성됩니다.

## 응답

```json
{
  "video_recording_id": "/inputs/3f1b7c6e-4e4d-4f6e-9a44-9d7a6f9d2d10/draft.webm",
  "extracted_frames": [
    {
      "image_id": "0d0a6e8c-...",
      "original_key": "/ai-finals/3f1b7c6e-4e4d-4f6e-9a44-9d7a6f9d2d10/final-001.png"
    }
  ]
}
```

## 현재 처리 흐름

1. `video_file`이 없거나 비어 있으면 거절합니다.
2. Spring이 S3 key를 고정 생성합니다.

   ```text
   /inputs/{sessionId}/draft.webm
   ```

3. `S3VideoClient.uploadVideo()`가 업로드된 MultipartFile 바이트를 그대로 S3에 저장합니다.
4. Redis `contents:{sessionId}`에 `video` 필드를 저장합니다.
5. FastAPI `POST /ai/sessions/{sessionId}/extract-frames`를 호출합니다.
6. `drafts` 결과를 받아 FastAPI `POST /ai/sessions/{sessionId}/final-edit`를 호출합니다.
7. Redis에 `video`, `status`, `draft:*`, `photo:*`를 저장합니다.
8. 최종 보정 이미지 목록을 `extracted_frames`로 반환합니다.

## webm/mp4 관련 현재 상태

현재 백엔드는 webm을 mp4로 변환하지 않습니다. 실제 바이트는 프론트가 보낸 webm이고, S3 object key도 `draft.webm`입니다. S3 `Content-Type`은 `videoFile.getContentType()`을 그대로 사용하므로 보통 `video/webm`입니다.

FastAPI도 변환하지 않습니다. 다운로드한 파일을 임시 경로 `input-video.webm`에 저장한 뒤 OpenCV로 읽습니다. OpenCV 빌드가 webm 코덱을 읽을 수 있어야 프레임 추출이 정상 동작합니다.

## 에러

- `INVALID_REQUEST`: 영상 파일이 없거나 비어 있습니다.
- `CONTENT_NOT_FOUND`: Redis 세션이 없어 `video` 저장에 실패했습니다.
- `AI_SERVER_FAILED`: FastAPI `extract-frames` 또는 `final-edit` 호출 실패입니다.
- 그 외 예외는 `INTERNAL_SERVER_ERROR`로 변환됩니다.

## 개선 제안

- 장기적으로는 업로드 파일의 실제 Content-Type에 따라 확장자를 결정하거나, 서버에서 명시적으로 mp4로 트랜스코딩해야 합니다.
- 비디오 업로드, 프레임 추출, 최종 보정을 모두 동기 처리하므로 요청 시간이 길어질 수 있습니다. 운영 안정성을 위해 비동기 작업 큐와 상태 조회 API로 분리하는 구조가 적합합니다.
