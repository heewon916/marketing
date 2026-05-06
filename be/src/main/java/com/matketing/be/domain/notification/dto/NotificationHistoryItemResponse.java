package com.matketing.be.domain.notification.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.domain.notification.enums.NotificationStatus;
import com.matketing.be.domain.notification.enums.NotificationType;
import java.time.OffsetDateTime;
import java.util.UUID;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class NotificationHistoryItemResponse {

    private UUID id;

    @JsonProperty("store_id")
    private UUID storeId;

    private NotificationType type;

    private NotificationStatus status;

    private String notification;

    @JsonProperty("scheduled_at")
    private OffsetDateTime scheduledAt;

    @JsonProperty("sent_at")
    private OffsetDateTime sentAt;

    @JsonProperty("retry_count")
    private int retryCount;

    @JsonProperty("failure_reason")
    private String failureReason;

    @JsonProperty("web_url")
    private String webUrl;

    @JsonProperty("reference_id")
    private UUID referenceId;

    public static NotificationHistoryItemResponse from(Notification notification) {
        return NotificationHistoryItemResponse.builder()
                .id(notification.getId())
                .storeId(notification.getStoreId())
                .type(notification.getType())
                .status(notification.getStatus())
                .notification(notification.getNotification())
                .scheduledAt(notification.getScheduledAt())
                .sentAt(notification.getSentAt())
                .retryCount(notification.getRetryCount())
                .failureReason(notification.getFailureReason())
                .webUrl(notification.getWebUrl())
                .referenceId(notification.getReferenceId())
                .build();
    }
}
