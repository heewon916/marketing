# API: 음성 인식(STT)

- **Endpoint**: `POST /api/v1/contents/stt`
- **Content-Type**: `multipart/form-data`
- **역할**: 클라이언트가 녹음한 음성 파일을 Clova STT로 전송해 텍스트 발화(`utterance`)로 변환합니다.

## 요청

```http
POST /api/v1/contents/stt
Content-Type: multipart/form-data
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| `audio_file` | File | 예 | 녹음 파일. 프론트 녹음은 보통 `audio/webm`입니다. |

## 응답

```json
{
  "status": "TEXT_RECOGNIZED",
  "utterance": "오늘 가게 신메뉴를 소개하고 싶어"
}
```

## 현재 처리 흐름

1. `ContentController.recognizeSpeech()`가 `audio_file`을 받습니다.
2. `ContentService.validateAudioFile()`에서 빈 파일 여부, Content-Type, 확장자를 검사합니다.
3. `ClovaSttClient.recognize()`를 호출합니다.
4. `ClovaSttAudioConverter`가 필요한 경우 `webm`, `m4a`, `mp4` 계열 입력을 `wav`로 변환해 Clova STT에 전달합니다.
5. 변환된 텍스트를 `TEXT_RECOGNIZED` 상태로 반환합니다.

## 허용 파일 기준

Content-Type 또는 확장자 중 하나가 허용 목록에 걸리면 통과합니다.

- 오디오 Content-Type: `audio/wav`, `audio/wave`, `audio/x-wav`, `audio/mpeg`, `audio/mp3`, `audio/mp4`, `audio/m4a`, `audio/x-m4a`, `audio/webm`
- 확장자: `wav`, `wave`, `mp3`, `m4a`, `mp4`, `webm`

## 에러

- `INVALID_AUDIO_FILE`: 파일이 없거나 비어 있거나, 허용되지 않은 타입입니다.
- `STT_FAILED`: Clova STT 호출 또는 오디오 변환에 실패했습니다.
- Multipart 자체가 깨진 경우 전역 예외 처리에서 multipart 에러로 응답합니다.

## 메모

현재 검증은 Content-Type과 확장자 기반입니다. 보안 강도를 높이려면 실제 파일 시그니처 검사나 미디어 파서 기반 검증을 추가해야 합니다.
