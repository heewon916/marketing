package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ContentImageDeleteRequestDto(
        @JsonProperty("session_id")
        String sessionId,
        @JsonProperty("deleted_image_key")
        String deletedImageKey
) {
}
