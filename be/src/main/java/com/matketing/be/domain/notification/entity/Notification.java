package com.matketing.be.domain.notification.entity;

import com.matketing.be.domain.notification.enums.NotificationStatus;
import com.matketing.be.domain.notification.enums.NotificationType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "notifications", indexes = {
        @Index(name = "idx_notifications_status_scheduled_at", columnList = "status, scheduled_at"),
        @Index(name = "idx_notifications_store_id", columnList = "store_id"),
        @Index(name = "idx_notifications_reference_id", columnList = "reference_id")
})
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Notification {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "store_id", nullable = false)
    private UUID storeId;

    @Column(name = "notification", columnDefinition = "TEXT", nullable = false)
    private String notification;

    @Column(name = "scheduled_at", nullable = false)
    private OffsetDateTime scheduledAt;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "type", nullable = false)
    private NotificationType type;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private NotificationStatus status;

    @Column(name = "sent_at")
    private OffsetDateTime sentAt;

    @Column(name = "retry_count", nullable = false)
    private int retryCount = 0;

    @Column(name = "failure_reason", columnDefinition = "TEXT")
    private String failureReason;

    @Column(name = "web_url", columnDefinition = "TEXT")
    private String webUrl;

    @Column(name = "reference_id")
    private UUID referenceId;

    @Builder
    public Notification(UUID storeId, String notification, OffsetDateTime scheduledAt, NotificationType type, NotificationStatus status, String webUrl, UUID referenceId) {
        this.storeId = storeId;
        this.notification = notification;
        this.scheduledAt = scheduledAt;
        this.type = type;
        this.status = status != null ? status : NotificationStatus.PENDING;
        this.webUrl = webUrl;
        this.referenceId = referenceId;
        this.retryCount = 0;
    }

    // 알림의 상태를 발송 처리 중(PROCESSING)으로 변경한다.
    public void markProcessing() {
        this.status = NotificationStatus.PROCESSING;
    }

    // 알림의 상태를 발송 완료(SENT)로 변경하고 발송 시간을 기록한다.
    public void markSent() {
        this.status = NotificationStatus.SENT;
        this.sentAt = OffsetDateTime.now();
        this.failureReason = null;
    }

    // 알림의 상태를 발송 실패(FAILED)로 변경하고 실패 사유를 기록한다.
    public void markFailed(String reason) {
        this.status = NotificationStatus.FAILED;
        this.failureReason = reason;
    }

    // 알림의 발송 재시도 횟수를 1 증가시킨다.
    public void increaseRetryCount() {
        this.retryCount += 1;
    }

    // 알림의 상태를 대기(PENDING)로 변경하고 다음 발송 예정 시간을 설정한다.
    public void reschedule(OffsetDateTime nextScheduledAt) {
        this.status = NotificationStatus.PENDING;
        this.scheduledAt = nextScheduledAt;
    }

    @PrePersist
    protected void onCreate() {
        this.createdAt = OffsetDateTime.now();
        this.updatedAt = OffsetDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = OffsetDateTime.now();
    }
}
