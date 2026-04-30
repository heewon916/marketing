package com.matketing.be.domain.notification.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Getter;

import java.time.OffsetDateTime;

@Getter
@Builder
public class TestNotificationSendResponse {
    private String status;

    @JsonProperty("sent_count")
    private int sentCount;

    @JsonProperty("failed_count")
    private int failedCount;

    @JsonProperty("sent_at")
    private OffsetDateTime sentAt;
}
