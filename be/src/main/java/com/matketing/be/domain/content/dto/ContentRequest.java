package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ContentRequest(
        @JsonProperty("request_id")
        String requestId,
        @JsonProperty("store_id")
        String storeId,
        String utterance
) {
}
