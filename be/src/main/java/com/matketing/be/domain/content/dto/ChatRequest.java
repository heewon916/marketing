package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record ChatRequest(
        @JsonProperty("request_id")
        @NotBlank(message = "request_id는 필수입니다.")
        @Pattern(
                regexp = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
                message = "request_id는 UUID 형식이어야 합니다."
        )
        String requestId,

        String utterance
) {
}
