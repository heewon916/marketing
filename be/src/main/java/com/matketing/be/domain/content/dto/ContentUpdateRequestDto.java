package com.matketing.be.domain.content.dto;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

public record ContentUpdateRequestDto(
        UUID sessionId,
        String caption,
        String instagramMediaId,
        String instagramPermalink,
        OffsetDateTime publishedAt,
        List<String> imageS3Keys,
        List<String> videoS3Keys
) {
}
