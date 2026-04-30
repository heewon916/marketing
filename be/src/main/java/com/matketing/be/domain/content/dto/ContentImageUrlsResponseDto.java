package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record ContentImageUrlsResponseDto(
        @JsonProperty("image_url")
        List<String> imageUrl
) {
}
