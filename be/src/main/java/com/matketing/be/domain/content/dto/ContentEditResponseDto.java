package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.OffsetDateTime;
import java.util.UUID;

public record ContentEditResponseDto(
        @JsonProperty("session_id")
        UUID sessionId,
        String caption,
        @JsonProperty("updated_at")
        OffsetDateTime updatedAt
) {
}
