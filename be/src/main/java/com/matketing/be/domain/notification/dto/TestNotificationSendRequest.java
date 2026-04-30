package com.matketing.be.domain.notification.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Getter
@NoArgsConstructor
public class TestNotificationSendRequest {
    @JsonProperty("user_id")
    @NotNull(message = "user_id is required")
    private UUID userId;

    @NotBlank(message = "title is required")
    private String title;

    @NotBlank(message = "body is required")
    private String body;

    @JsonProperty("web_url")
    private String webUrl;
}
