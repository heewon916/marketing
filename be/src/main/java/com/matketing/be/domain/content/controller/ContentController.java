package com.matketing.be.domain.content.controller;

import com.matketing.be.domain.content.dto.ContentEditRequestDto;
import com.matketing.be.domain.content.dto.ContentEditResponseDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteResponseDto;
import com.matketing.be.domain.content.dto.ContentImageUrlsResponseDto;
import com.matketing.be.domain.content.dto.ContentRequest;
import com.matketing.be.domain.content.dto.ContentResponseDto;
import com.matketing.be.domain.content.dto.SttResponse;
import com.matketing.be.domain.content.service.ContentService;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
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
     * 게시물 이미지 조회 API
     * @param contentId TODO sessionId가 아니어도 되는가
     * @return ContentImageUrlsResponseDto 해당 게시물의 이미지 s3 url을 리턴한다
     */
    @GetMapping("/{contentId}/images")
    public ContentImageUrlsResponseDto getContentImages(@PathVariable Long contentId) {
        return contentService.getContentImages(contentId);
    }


    /**
     * 게시물 이미지 삭제 API
     * TODO 이미지 정보 삭제는 redis에서 이루어진다. 이 로직으로 수정이 필요해보인다.
     * @param contentId
     * @param imageId
     * @return
     */
    @DeleteMapping("/{contentId}/images/{imageId}")
    public ContentImageDeleteResponseDto deleteContentImage(
            @PathVariable Long contentId,
            @PathVariable UUID imageId  // TODO UUID..?
    ) {
        return contentService.deleteContentImage(contentId, imageId);
    }

    /**
     * 게시물 내용 조회 API
     * - 캡션, 이미지 조회
     * @param contentId
     * @return
     */
    @GetMapping("/{contentId}")
    public ContentResponseDto getContent(@PathVariable Long contentId) {
        return contentService.getContent(contentId);
    }

    // 현재 스키마 기준으로 게시물 텍스트는 caption만 수정할 수 있다.
    @PutMapping("/{contentId}/edit")
    public ContentEditResponseDto updateContent(
            @PathVariable Long contentId,
            @RequestBody ContentEditRequestDto requestDto
    ) {
        return contentService.updateContent(contentId, requestDto);
    }

    // TODO JWT 인증 필터가 적용되면 이 함수는 삭제하고 SecurityContext의 실제 user_name을 주도록 바꿔야 한다.
    private String getCurrentUserId(Authentication authentication) {
        if (authentication != null && authentication.getName() != null && !authentication.getName().isBlank()) {
            return authentication.getName();
        }
        return "00000000-0000-0000-0000-000000000000";
    }
}
