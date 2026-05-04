package com.matketing.be.domain.content.service;

import com.matketing.be.domain.content.dto.ContentEditRequestDto;
import com.matketing.be.domain.content.dto.ContentEditResponseDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteResponseDto;
import com.matketing.be.domain.content.dto.ContentImageUrlsResponseDto;
import com.matketing.be.domain.content.dto.ContentResponseDto;
import com.matketing.be.domain.content.entity.Content;
import com.matketing.be.domain.content.entity.ContentImage;
import com.matketing.be.domain.content.repository.ContentImageRepository;
import com.matketing.be.domain.content.repository.ContentRepository;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ContentService {

    private final ContentRepository contentRepository;
    private final ContentImageRepository contentImageRepository;

    @Transactional(readOnly = true)
    public ContentImageUrlsResponseDto getContentImages(Long contentId) {
        Content content = getContentWithRelations(contentId);

        return new ContentImageUrlsResponseDto(
                content.getImages().stream()
                        .map(ContentImage::getS3Key)
                        .toList()
        );
    }

    @Transactional
    public ContentImageDeleteResponseDto deleteContentImage(Long contentId, UUID imageId) {
        // 현재 엔티티에는 soft delete 플래그가 없어 실제 삭제로 처리한다.
        findContentById(contentId);

        ContentImage contentImage = contentImageRepository.findByIdAndContent_Id(imageId, contentId)
                .orElseThrow(() -> new BusinessException(ErrorCode.CONTENT_IMAGE_NOT_FOUND));

        contentImageRepository.delete(contentImage);

        long remainingImages = contentImageRepository.countByContent_Id(contentId);
        return new ContentImageDeleteResponseDto(true, remainingImages);
    }

    @Transactional(readOnly = true)
    public ContentResponseDto getContent(Long contentId) {
        return ContentResponseDto.from(getContentWithRelations(contentId));
    }

    @Transactional
    public ContentEditResponseDto updateContent(Long contentId, ContentEditRequestDto requestDto) {
        Content content = findContentById(contentId);

        // 현재 스키마에는 status/hashtags/updatedAt이 없어 caption만 수정한다.
        content.updateCaption(requestDto.caption());

        return ContentEditResponseDto.from(content);
    }

    private Content findContentById(Long contentId) {
        return contentRepository.findById(contentId)
                .orElseThrow(() -> new BusinessException(ErrorCode.CONTENT_NOT_FOUND));
    }

    private Content getContentWithRelations(Long contentId) {
        return contentRepository.findWithImagesAndVideoRecordingsById(contentId)
                .orElseThrow(() -> new BusinessException(ErrorCode.CONTENT_NOT_FOUND));
    }
}
