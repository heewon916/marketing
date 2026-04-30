package com.matketing.be.domain.content.dto;

import jakarta.validation.constraints.NotNull;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

public record ContentCreateRequestDto(
        @NotNull UUID storeId,
        UUID sessionId,
        String caption,
        String instagramMediaId,
        String instagramPermalink,
        OffsetDateTime publishedAt,
        List<String> imageS3Keys,
        List<String> videoS3Keys
) {
}
