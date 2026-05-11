package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record AiFinalEditRequest(
        @JsonProperty("session_id")
        String sessionId,
        List<String> drafts
) {
}
