package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;

public record AiProcessUtteranceRequest(
        @JsonIgnore
        String sessionId,
        @JsonProperty("store_id")
        String storeId,
        String utterance,
        @JsonProperty("owner_persona")
        String ownerPersona,
        String date,
        AiWeatherRequest weather
) {
}
