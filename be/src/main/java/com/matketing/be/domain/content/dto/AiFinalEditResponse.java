package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record AiFinalEditResponse(
        @JsonProperty("session_id")
        String sessionId,
        String status,
        List<String> results
) {
}
