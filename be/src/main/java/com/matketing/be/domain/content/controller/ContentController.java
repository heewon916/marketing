package com.matketing.be.domain.content.controller;

import com.matketing.be.domain.content.dto.ChatRequest;
import com.matketing.be.domain.content.dto.ChatResponse;
import com.matketing.be.domain.content.dto.ContentDraftResponseDto;
import com.matketing.be.domain.content.dto.ContentEditRequestDto;
import com.matketing.be.domain.content.dto.ContentEditResponseDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteRequestDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteResponseDto;
import com.matketing.be.domain.content.dto.ContentImageUrlsResponseDto;
import com.matketing.be.domain.content.dto.ContentPublishResponseDto;
import com.matketing.be.domain.content.dto.ContentPublishStatusResponseDto;
import com.matketing.be.domain.content.dto.ContentRequest;
import com.matketing.be.domain.content.dto.ContentVideoResponseDto;
import com.matketing.be.domain.content.dto.SttResponse;
import com.matketing.be.domain.content.service.ContentService;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/contents")
public class ContentController {

    private final ContentService contentService;

    /**
     * S3 저장 규칙
     * 1. 사용자가 처음 찍은 영상 : /inputs/{session-id}/draft.mp4
     * 2. AI가 처음 프레임 추출한 drafts : /ai-drafts/{session-id}/draft-001.jpg
     * 3. AI가 최종 편집한 사진 : /ai-finals/{session-id}/final-001.jpg
     * 4. 레퍼런스 사진 : /references/{owner_persona}/{reference_id}/001.jpg
     */

    /**
     * 사용자 발화 처리 API
     * Clova STT API
     * 역할: multipart 파라미터 service, client로 전달
     * 응답: 최종 utterance, status=TEXT_RECOGNIZED
     * @param audioFile
     * @return
     */
    @PostMapping("/stt")
    public SttResponse recognizeSpeech(@RequestPart(value = "audio_file", required = false) MultipartFile audioFile) {
        return contentService.recognizeSpeech(audioFile);
    }

    /**
     * 게시물 캡션 생성 API
     * - request_id가 포함된 기존 요청: Redis 멱등성 처리 후 FastAPI 캡션 생성 트리거
     * - request_id가 없는 신규 요청: store/utterance 기반 AI 게시글 생성 참고 JSON 반환
     * - store_id가 없으면 인증 사용자 기준으로 등록된 매장을 조회한다.
     * request body:
     * {
     * 	"request_id": "9d5b4b52-78f2-4f7e-8c10-4a04bb5a6b1b",
     * 	"utterance": "오늘 가게에 있는 찻잔, 곰돌이 인형, 원목 찬장을 자랑하고 싶어"
     * }
     *
     * response body:
     * {
     * 	"session_id": "3f1b7c6e-4e4d-4f6e-9a44-9d7a6f9d2d10",
     * 	"status": "TEXT_GENERATED",
     * 	"guide_text": "찻잔, 곰돌이 인형, 원목 찬장이 모두 잘 보이도록 예쁘게 찍어주세요!",
     * 	"caption": "비 내리는 월요일 오후, 따뜻한 #생강차 한 잔 어떠세요?"
     * }
     *
     * @param request store_id, request_id(선택), 최종 utterance
     * @return 기존 캡션 생성 응답(ChatResponse) 또는 참고정보 응답(ContentResponse)
     */
    @PostMapping("/caption")
    public Object createTextContent(@RequestBody ContentRequest request) {
        return contentService.createCaption(request);
    }

    /**
     * 임시 저장 게시물 이미지 조회 API
     * request body: {}
     * response body:
     * {
     * 		"session_id": uuid,
     *      "image_url": [
     * 	        {
     * 	            "image_key": "photo:{no}",
     * 			    "image_url" : "/ai-finals/{session-id}/final-001.jpg"
     *          },
     *      ]
     * }
     * @param sessionId
     * @return List<String> imageUrl
     */
    @GetMapping("/{sessionId}/images")
    public ContentImageUrlsResponseDto getContentImages(@PathVariable UUID sessionId) {
        return contentService.getContentImages(sessionId);
    }


    /**
     * 임시저장 게시물 이미지 삭제 API
     * redis: `contents:{session_id}:photo:{no}` 삭제
     * request body:
     * {
     * 	"session_id": uuid,
     * 	"deleted_image_key": redis 키 값
     * }
     * response body:
     * {
     *   "success": true,
     *   "remaining_images": 2 // 남은 이미지 개수만 반환
     * }
     * @param sessionId
     * @param request
     * @return
     */
    @DeleteMapping("/{sessionId}/images/delete")
    public ContentImageDeleteResponseDto deleteContentImage(
            @PathVariable UUID sessionId,
            @RequestBody ContentImageDeleteRequestDto request
    ) {
        return contentService.deleteContentImage(sessionId, request.deletedImageKey());
    }

    /**
     * 임시저장 게시물 텍스트 수정 API
     * request body:
     * {
     *   "caption": "수정된 무언가"
     * }
     * response body:
     * {
     *   "session_id": "uuid",
     *   "caption": " …. ",
     *   "updated_at": "2026-04-23T10:00:00Z"
     * }
     * @param sessionId 수정할 게시물의 sessionId
     * @param requestDto
     * @return
     */
    @PatchMapping("/{sessionId}/edit")
    public ContentEditResponseDto updateContent(
            @PathVariable UUID sessionId,
            @RequestBody ContentEditRequestDto requestDto
    ) {
        return contentService.updateContent(sessionId, requestDto);
    }

    /**
     * 임시저장인 게시물 내용 조회 API
     * - 응답에는 캡션, 이미지, 인스타 아이디, 인스타 프로필
     * - 인스타 아이디랑 인스타 프로필도 응답에 포함시켜야 함
     *
     * request body:{}
     * response body:
     * {
     *   "sessionId": "uuid",
     *   "status": "draft",
     *   "caption": "...",
     *   "images": [
     *          {
     *          "id" : "uuid",
     *          "filtered_url": "s3://...",
     *          "display_order": 1
     *          }
     *      ],
     *   "instagramUsername": "".
     *   "instagramProfileImageUrl": ""
     * }
     * @param sessionId
     * @return
     */
    @GetMapping("/{sessionId}")
    public ContentDraftResponseDto getContent(@PathVariable UUID sessionId) {
        return contentService.getContent(sessionId);
    }

    /**
     * 게시물 발행 API
     * @PostMapping("/{sessionId}/publish")
     * 발행하기 버튼을 누르면 조회됩니다.
     * request body: {}
     * response body:
     * {
     *      "content_id":"uuid",
     *      "publish_progress": "queued",
     *      "message": "발행이 시작되었습니다"
     * }
     */
    @PostMapping("/{sessionId}/publish")
    public ContentPublishResponseDto publishContent(@PathVariable UUID sessionId) {
        return contentService.publishContent(sessionId);
    }

    /**
     * 게시물 발행 상태 조회 API
     * @GetMapping("/{session_id}/publish/status")
     * 발행 상태를 조회합니다. 주기적으로 프론트에서 요청할 수 있습니다.
     * 만약 발행이 성공되면 DB에 저장하고 해당 응답을 프론트에게 전달합니다.
     * Redis에 저장되어 있던 관련 세션 정보는 남깁니다.
     *
     * request body: {}
     * response body:
     * {
     * 	    "content_id": "uuid",
     *      "publish_progress": "completed",
     * 	    "instagram_media_id":  "17918...",
     * 	    "instagram_permalink": "https://instagram.com/p/..."
     * }
     */
    @GetMapping("/{sessionId}/publish/status")
    public ContentPublishStatusResponseDto getPublishStatus(@PathVariable UUID sessionId) {
        return contentService.getPublishStatus(sessionId);
    }

    /**
     * 비디오 추출 API
     * @PostMapping("/{session_id}/video")
     * 프론트로부터 mp4파일을 받고, s3에 저장합니다.
     * ai 모델을 내부적으로 호출해 프레임을 추출, 최종 편집합니다.
     *
     * request body:
     * (multipart/form-data)
     *     video_file: File
     * 		session_id: uuid
     *
     * response body:
     * {
     * 	    "video_recording_id": "video s3 key",
     * 	    "extracted_frames":	[
     * 	        {
     * 	            "image_id": "uuid",
     * 	            "original_key":	"s3_url"
     * 	        },
     *      ]
     * }
     *
     * 1. AI 비디오 프레임 추출 호출 →  /ai/sessions/{session_id}/extract-frames
     * request body:
     * {
     *  "session_id": "uuid",
     *  "video": "/inputs/{session-id}/test-video.mp4"
     * }
     * response body:
     * -> s3 url을 돌려 받습니다.
     * {
     * 	"session_id": "uuid",
     * 	"status" : "FRAME_EXTRACTED",
     * 	"drafts": [
     * 		"/ai-drafts/session-123/draft-001.jpg",
     * 		"/ai-drafts/session-123/draft-002.jpg"
     * 	]
     * }
     *
     * 2. AI 사진 최종 편집 호출 → /ai/sessions/{session_id}/final-edit
     *
     * request body:
     * {
     * 	"session_id": "uuid",
     * 	"drafts" : [
     * 		"/ai-drafts/session-123/draft-001.jpg",
     * 		"/ai-drafts/session-123/draft-002.jpg"
     * 	]
     * }
     *
     * response body:
     * - AI가 redis에 저장합니다. 우리는 results를 최종 /api/v1/contents/{sessionId}/video의 응답에 포함하게 됩니다.
     * contents:{sessionId}:
     * {
     * 	"session_id": "uuid",
     * 	"status" : "PHOTO_EDITED",
     * 	"results":
     * 		[
     * 			"/ai-finals/session-123/final-001.jpg",
     * 			"/ai-finals/session-123/final-002.jpg"
     * 		]
     * }
     *
     */
    @PostMapping("/{sessionId}/video")
    public ContentVideoResponseDto processVideo(
            @PathVariable UUID sessionId,
            @RequestPart("video_file") MultipartFile videoFile
    ) {
        return contentService.processVideo(sessionId, videoFile);
    }
}
