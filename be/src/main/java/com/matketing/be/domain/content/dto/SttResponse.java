package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record SttResponse(
        String utterance,
        @JsonProperty("status")
        String status
) {
}
