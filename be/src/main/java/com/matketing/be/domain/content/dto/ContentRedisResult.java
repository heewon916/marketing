package com.matketing.be.domain.content.dto;

import com.matketing.be.domain.content.enums.ContentStatus;

public record ContentRedisResult(
        String sessionId,
        ContentStatus status,
        String guideText,
        String caption
) {
}
