package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ContentResponse(
        @JsonProperty("store_id")
        String storeId,
        String utterance,
        @JsonProperty("owner_persona")
        String ownerPersona,
        String date,
        AiWeatherRequest weather
) {
}
