package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.dto.ImmediateNotificationResponse;
import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.domain.notification.enums.NotificationType;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.OffsetDateTime;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class ImmediateNotificationService {

    private final NotificationCommandService notificationCommandService;
    private final NotificationQueueService notificationQueueService;
    private final NotificationMessageResolver notificationMessageResolver;

    @Transactional
    public ImmediateNotificationResponse sendImmediate(UUID storeId, NotificationType type, UUID referenceId) {
        if (type != NotificationType.POSTING_SUCCESS && type != NotificationType.POSTING_FAILED) {
            throw new BusinessException(ErrorCode.INVALID_IMMEDIATE_NOTIFICATION_TYPE);
        }

        String notificationText = notificationMessageResolver.resolveNotificationText(type);
        String webUrl = notificationMessageResolver.resolveWebUrl(type, referenceId);

        Notification notification = notificationCommandService.createPendingNotification(
                storeId,
                type,
                notificationText,
                OffsetDateTime.now(),
                webUrl,
                referenceId
        );

        try {
            notificationQueueService.enqueue(notification.getId());
        } catch (Exception e) {
            log.error("Failed to enqueue immediate notification: {}", notification.getId(), e);
            notificationCommandService.markFailed(notification.getId(), "Failed to enqueue immediate notification: " + e.getMessage());
            throw new BusinessException(ErrorCode.IMMEDIATE_NOTIFICATION_ENQUEUE_FAILED);
        }

        return new ImmediateNotificationResponse(
                "success",
                notification.getId(),
                OffsetDateTime.now()
        );
    }
}
