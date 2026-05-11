package com.matketing.be.domain.content.controller;

import com.matketing.be.domain.content.dto.ChatRequest;
import com.matketing.be.domain.content.dto.ChatResponse;
import com.matketing.be.domain.content.dto.ContentEditRequestDto;
import com.matketing.be.domain.content.dto.ContentEditResponseDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteRequestDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteResponseDto;
import com.matketing.be.domain.content.dto.ContentImageUrlsResponseDto;
import com.matketing.be.domain.content.dto.ContentRequest;
import com.matketing.be.domain.content.dto.ContentResponseDto;
import com.matketing.be.domain.content.dto.SttResponse;
import com.matketing.be.domain.content.service.ContentService;
import jakarta.validation.Valid;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/contents")
public class ContentController {

    private final ContentService contentService;

    /**
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
     * @param request store_id, request_id(선택), 최종 utterance
     * @param authentication TODO SecurityContext에서 인증된 사용자로 변경
     * @return 기존 캡션 생성 응답(ChatResponse) 또는 참고정보 응답(ContentResponse)
     */
    @PostMapping("/caption")
    public Object createTextContent(
            @RequestBody ContentRequest request,
            Authentication authentication
    ) {
        // Controller는 인증 사용자 식별자만 Service에 전달하고, 요청 형태별 분기는 ContentService에서 처리한다.
        return contentService.createCaption(request, getCurrentUserId(authentication));
    }

    /**
     * 임시 저장 게시물 이미지 조회 API
     * @param sessionId
     * @return List<String> imageUrl
     */
    @GetMapping("/{sessionId}/images")
    public ContentImageUrlsResponseDto getContentImages(@PathVariable UUID sessionId) {
        return contentService.getContentImages(sessionId);
    }


    /**
     * 임시저장 게시물 이미지 삭제 API
     * TODO 이미지 정보 삭제는 redis에서 이루어진다. 이 로직으로 수정이 필요해보인다.
     * TODO request body로 전달받는 이미지 url 삭제는 param에 어떻게 반영해야 할까.
     * request body:
     * {
     *     "image_url": "ai-finals/{sessionId}/final-001.jpg" // 삭제할 이미지의 s3 url
     * }
     * @param sessionId
     * @param imageUrl
     * @return
     */
    @DeleteMapping("/{sessionId}/images/delete")
    public ContentImageDeleteResponseDto deleteContentImage(
            @PathVariable UUID sessionId,
            @RequestBody ContentImageDeleteRequestDto request
    ) {
        return contentService.deleteContentImage(sessionId, request.imageUrl());
    }

    /**
     * 임시저장 게시물 텍스트 수정 API
     * - 캡션 수정만 가능하다
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
     * @param sessionId
     * @return
     */
    @GetMapping("/{sessionId}")
    public ContentResponseDto getContent(@PathVariable UUID sessionId) {
        return contentService.getContent(sessionId);
    }


    // 현재 스키마 기준으로 게시물 텍스트는 caption만 수정할 수 있다. - redis 존재


    // TODO 게시물 발행 API 로직 추가
    // return할 때 최종 캡션, 이미지를 줘야 한다. 그리고 instagram 리다이렉트 url도
    // @PostMapping("/{sessionId}/publish")
    /*
      1. session_id로 Redis contents:{sessionId} 조회
      2. caption, image urls, video url, status 검증
      3. Instagram 발행 API 호출
      4. 성공하면 DB contents 생성
      5. contents_images, video_recordings 생성
      6. instagram_media_id, instagram_permalink, published_at 저장
      7. 응답으로 content_id 반환
      8. Redis 세션은 삭제하거나 PUBLISHED 상태로 TTL 부여

      현재 계획된 api는 2가지
      1. /api/v1/contents/{sessionId}/publish -> 응답: {content_id: , publish_progress: , message: "발행이 시작되었습니다"}
      2. /api/v1/contents/{sessionId}/publish/status -> 응답: {content_id: , publish_progress: , instagram_media_id: , instagram_permalink: }
     */

    /**
     * 최종발행된 게시물의 링크 조회 API
     * - 오로지 발행된 인스타그램의 perm_link만 주면 될 듯 싶다
     * @param contentId
     * @return
     */
    @GetMapping("/published/{contentId}")
    public ContentResponseDto getPublishedContent(@PathVariable Long contentId) {
        return contentService.getPublishedContent(contentId);
    }

    // TODO JWT 인증 필터가 적용되면 이 함수는 삭제하고 SecurityContext의 실제 user_name을 주도록 바꿔야 한다.
    private String getCurrentUserId(Authentication authentication) {
        if (authentication != null && authentication.getName() != null && !authentication.getName().isBlank()) {
            return authentication.getName();
        }
        return "00000000-0000-0000-0000-000000000000";
    }
}
