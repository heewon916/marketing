package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.UUID;

public record ContentDraftResponseDto(
        @JsonProperty("session_id")
        UUID sessionId,
        String status,
        String caption,
        List<ImageItem> images,
        @JsonProperty("instagram_username")
        String instagramUsername,
        @JsonProperty("instagram_profile_image_url")
        String instagramProfileImageUrl
) {

    public record ImageItem(
            String id,
            @JsonProperty("filtered_url")
            String filteredUrl,
            @JsonProperty("display_order")
            int displayOrder
    ) {
    }
}
