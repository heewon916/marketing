package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ContentImageDeleteResponseDto(
        boolean success,
        @JsonProperty("remaining_images")
        long remainingImages
) {
}
