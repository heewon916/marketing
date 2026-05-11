package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiExtractFramesRequest(
        @JsonProperty("session_id")
        String sessionId,
        String video
) {
}
