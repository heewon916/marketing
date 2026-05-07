package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiProcessUtteranceResponse(
        @JsonProperty("session_id")
        String sessionId,
        String status,
        @JsonProperty("guide_text")
        String guideText,
        String caption
) {
}
