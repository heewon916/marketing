package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.matketing.be.domain.content.enums.ContentStatus;

public record ChatResponse(
        @JsonProperty("session_id")
        String sessionId,
        ContentStatus status,
        @JsonProperty("guide_text")
        String guideText,
        String caption
) {
}
