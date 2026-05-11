package com.matketing.be.domain.content.dto;

import com.matketing.be.domain.content.entity.Content;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

/**
 * 최종 발행 이후의 게시물 응답
 * @param id
 * @param storeId
 * @param sessionId
 * @param caption
 * @param instagramMediaId
 * @param instagramPermalink
 * @param publishedAt
 * @param isDeleted
 * @param deletedAt
 * @param createdAt
 * @param images
 * @param videoRecordings
 */
public record ContentResponseDto(
        Long id,
        UUID storeId,
        UUID sessionId,
        String caption,
        String instagramMediaId,
        String instagramPermalink,
        OffsetDateTime publishedAt,
        Boolean isDeleted,
        OffsetDateTime deletedAt,
        OffsetDateTime createdAt,
        List<ContentImageResponseDto> images,
        List<VideoRecordingResponseDto> videoRecordings
) {

    public static ContentResponseDto from(Content content) {
        return new ContentResponseDto(
                content.getId(),
                content.getStoreId(),
                content.getSessionId(),
                content.getCaption(),
                content.getInstagramMediaId(),
                content.getInstagramPermalink(),
                content.getPublishedAt(),
                content.getIsDeleted(),
                content.getDeletedAt(),
                content.getCreatedAt(),
                content.getImages().stream()
                        .map(ContentImageResponseDto::from)
                        .toList(),
                content.getVideoRecordings().stream()
                        .map(VideoRecordingResponseDto::from)
                        .toList()
        );
    }
}
