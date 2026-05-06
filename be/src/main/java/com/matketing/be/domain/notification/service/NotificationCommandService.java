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
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;

@Service
@RequiredArgsConstructor
@Transactional
public class NotificationCommandService {

    private final NotificationRepository notificationRepository;

    // 새로운 대기(PENDING) 상태의 알림을 생성하고 저장한다.
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

    // 알림의 상태를 처리 중(PROCESSING)으로 변경한다.
    public void markProcessing(UUID notificationId) {
        Notification notification = getNotification(notificationId);
        notification.markProcessing();
    }

    // 알림의 상태를 발송 완료(SENT)로 변경한다.
    public void markSent(UUID notificationId) {
        Notification notification = getNotification(notificationId);
        notification.markSent();
    }

    // 알림의 상태를 발송 실패(FAILED)로 변경하고 실패 사유를 저장한다.
    public void markFailed(UUID notificationId, String failureReason) {
        Notification notification = getNotification(notificationId);
        notification.markFailed(failureReason);
    }

    // 알림의 재시도 횟수를 증가시킨다.
    public void increaseRetryCount(UUID notificationId) {
        Notification notification = getNotification(notificationId);
        notification.increaseRetryCount();
    }

    // 알림의 발송 예정 시간을 재설정하고 대기(PENDING) 상태로 변경한다.
    public void reschedule(UUID notificationId, OffsetDateTime nextScheduledAt) {
        Notification notification = getNotification(notificationId);
        notification.reschedule(nextScheduledAt);
    }

    private Notification getNotification(UUID notificationId) {
        return notificationRepository.findById(notificationId)
                .orElseThrow(() -> new BusinessException(ErrorCode.NOTIFICATION_NOT_FOUND));
    }
}
