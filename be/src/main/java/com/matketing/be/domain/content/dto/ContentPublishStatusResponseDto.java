package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ContentPublishStatusResponseDto(
        @JsonProperty("content_id")
        String contentId,
        @JsonProperty("publish_progress")
        String publishProgress,
        @JsonProperty("instagram_media_id")
        String instagramMediaId,
        @JsonProperty("instagram_permalink")
        String instagramPermalink
) {
}
