package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.UUID;

public record ContentImageUrlsResponseDto(
        @JsonProperty("session_id")
        UUID sessionId,
        @JsonProperty("image_url")
        List<ImageUrlItem> imageUrl
) {

    public record ImageUrlItem(
            @JsonProperty("image_key")
            String imageKey,
            @JsonProperty("image_url")
            String imageUrl
    ) {
    }
}
