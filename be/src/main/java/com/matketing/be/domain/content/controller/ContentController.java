package com.matketing.be.domain.content.controller;

import com.matketing.be.domain.content.dto.ContentEditRequestDto;
import com.matketing.be.domain.content.dto.ContentEditResponseDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteResponseDto;
import com.matketing.be.domain.content.dto.ContentImageUrlsResponseDto;
import com.matketing.be.domain.content.dto.ContentResponseDto;
import com.matketing.be.domain.content.service.ContentService;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/contents")
public class ContentController {

    private final ContentService contentService;

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
}
