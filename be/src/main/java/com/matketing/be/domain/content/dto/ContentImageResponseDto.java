package com.matketing.be.domain.content.dto;

import com.matketing.be.domain.content.entity.ContentImage;
import java.util.UUID;

public record ContentImageResponseDto(
        UUID id,
        String s3Key
) {

    public static ContentImageResponseDto from(ContentImage contentImage) {
        return new ContentImageResponseDto(contentImage.getId(), contentImage.getS3Key());
    }
}
