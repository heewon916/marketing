package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.domain.notification.enums.NotificationStatus;
import com.matketing.be.domain.notification.enums.NotificationType;
import com.matketing.be.domain.notification.repository.NotificationRepository;
import java.time.OffsetDateTime;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional
public class NotificationCommandService {

    private final NotificationRepository notificationRepository;

    public Notification createPendingNotification(UUID storeId, NotificationType type, String notificationText, OffsetDateTime scheduledAt, String webUrl, UUID referenceId) {
        Notification notification = Notification.builder()
                .storeId(storeId)
                .notification(notificationText)
                .scheduledAt(scheduledAt)
                .type(type)
                .status(NotificationStatus.PENDING)
                .webUrl(webUrl)
                .referenceId(referenceId)
                .build();
        return notificationRepository.save(notification);
    }

    public void markProcessing(UUID notificationId) {
        Notification notification = getNotification(notificationId);
        notification.markProcessing();
    }

    public void markSent(UUID notificationId) {
        Notification notification = getNotification(notificationId);
        notification.markSent();
    }

    public void markFailed(UUID notificationId, String failureReason) {
        Notification notification = getNotification(notificationId);
        notification.markFailed(failureReason);
    }

    public void increaseRetryCount(UUID notificationId) {
        Notification notification = getNotification(notificationId);
        notification.increaseRetryCount();
    }

    public void reschedule(UUID notificationId, OffsetDateTime nextScheduledAt) {
        Notification notification = getNotification(notificationId);
        notification.reschedule(nextScheduledAt);
    }

    private Notification getNotification(UUID notificationId) {
        return notificationRepository.findById(notificationId)
                .orElseThrow(() -> new IllegalArgumentException("Notification not found with id: " + notificationId));
    }
}
