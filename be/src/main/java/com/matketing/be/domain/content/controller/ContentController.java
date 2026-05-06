package com.matketing.be.domain.content.controller;

import com.matketing.be.domain.content.dto.ChatRequest;
import com.matketing.be.domain.content.dto.ChatResponse;
import com.matketing.be.domain.content.dto.ContentEditRequestDto;
import com.matketing.be.domain.content.dto.ContentEditResponseDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteResponseDto;
import com.matketing.be.domain.content.dto.ContentImageUrlsResponseDto;
import com.matketing.be.domain.content.dto.ContentResponseDto;
import com.matketing.be.domain.content.dto.SttResponse;
import com.matketing.be.domain.content.service.ContentService;
import jakarta.validation.Valid;
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

    // 음성 입력 단계의 API 진입점이다.
    // Controller는 multipart 파라미터만 받고, 파일 유효성 검증과 Clova STT 호출은 Service/Client 계층에 위임한다.
    // 응답에는 다음 단계에서 사용할 최종 발화 텍스트와 TEXT_RECOGNIZED 상태만 포함한다.
    @PostMapping("/stt")
    public SttResponse recognizeSpeech(@RequestPart(value = "audio_file", required = false) MultipartFile audioFile) {
        return contentService.recognizeSpeech(audioFile);
    }

    // 최종 발화로 AI 게시물 텍스트 생성을 요청하는 API 진입점이다.
    // 같은 사용자의 같은 request_id는 Redis 멱등성 key로 하나의 session_id에 묶인다.
    // 최초 요청이면 FastAPI 생성을 트리거하고, 중복 요청이면 FastAPI를 다시 호출하지 않고 Redis에 남은 결과를 반환한다.
    @PostMapping("/caption")
    public ChatResponse createTextContent(
            @Valid @RequestBody ChatRequest request,
            Authentication authentication
    ) {
        return contentService.createTextContent(request, getCurrentUserId(authentication));
    }

    // 게시물에 연결된 이미지 s3Key 목록을 조회한다.
    @GetMapping("/{contentId}/images")
    public ContentImageUrlsResponseDto getContentImages(@PathVariable Long contentId) {
        return contentService.getContentImages(contentId);
    }

    // 현재 엔티티 구조에는 soft delete가 없어 실제 삭제로 동작한다.
    @DeleteMapping("/{contentId}/images/{imageId}")
    public ContentImageDeleteResponseDto deleteContentImage(
            @PathVariable Long contentId,
            @PathVariable UUID imageId
    ) {
        return contentService.deleteContentImage(contentId, imageId);
    }

    // 현재 Content 엔티티와 연관된 이미지/영상 정보를 함께 반환한다.
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

    private String getCurrentUserId(Authentication authentication) {
        // Redis 멱등성 key는 사용자 단위로 분리되어야 하므로 인증 주체의 name을 사용자 식별자로 사용한다.
        // 현재 프로젝트에는 JWT 인증 필터가 완성되어 있지 않아, 인증이 비어 있으면 임시 고정 ID로 동작한다.
        if (authentication != null && authentication.getName() != null && !authentication.getName().isBlank()) {
            return authentication.getName();
        }

        // TODO: JWT 인증 필터 적용 후 SecurityContext의 실제 user_id를 사용한다.
        return "00000000-0000-0000-0000-000000000000";
    }
}
