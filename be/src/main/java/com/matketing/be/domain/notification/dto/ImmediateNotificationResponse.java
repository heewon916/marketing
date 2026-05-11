package com.matketing.be.domain.notification.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.OffsetDateTime;
import java.util.UUID;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class ImmediateNotificationResponse {

    private String status;

    @JsonProperty("notification_id")
    private UUID notificationId;

    @JsonProperty("sent_at")
    private OffsetDateTime sentAt;
}
