package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ContentPublishResponseDto(
        @JsonProperty("content_id")
        String contentId,
        @JsonProperty("publish_progress")
        String publishProgress,
        String message
) {
}
