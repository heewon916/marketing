package com.matketing.be.domain.content.dto;

import com.matketing.be.domain.content.entity.Content;
import java.time.OffsetDateTime;
import java.util.UUID;

public record ContentSummaryResponseDto(
        Long id,
        UUID storeId,
        String caption,
        String instagramPermalink,
        OffsetDateTime publishedAt,
        Boolean isDeleted,
        OffsetDateTime createdAt,
        int imageCount,
        int videoCount
) {

    public static ContentSummaryResponseDto from(Content content) {
        return new ContentSummaryResponseDto(
                content.getId(),
                content.getStoreId(),
                content.getCaption(),
                content.getInstagramPermalink(),
                content.getPublishedAt(),
                content.getIsDeleted(),
                content.getCreatedAt(),
                content.getImages().size(),
                content.getVideoRecordings().size()
        );
    }
}
