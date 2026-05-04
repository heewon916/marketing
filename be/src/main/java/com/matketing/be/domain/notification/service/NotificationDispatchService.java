package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.dto.DispatchResult;
import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationDispatchService {

    private final NotificationQueryService notificationQueryService;
    private final NotificationCommandService notificationCommandService;
    private final NotificationQueueService notificationQueueService;

    // 발송 예정 시간이 지난 알림을 조회해 상태를 변경하고 Redis Queue에 적재한다.
    public DispatchResult dispatchDueNotifications(int batchSize) {
        if (batchSize <= 0) {
            throw new BusinessException(ErrorCode.INVALID_NOTIFICATION_BATCH_SIZE);
        }

        List<Notification> dueNotifications = notificationQueryService.findDueNotifications(batchSize);

        int dispatchedCount = 0;
        int failedCount = 0;

        for (Notification notification : dueNotifications) {
            try {
                notificationCommandService.markProcessing(notification.getId());
                notificationQueueService.enqueue(notification.getId());
                dispatchedCount++;
            } catch (Exception e) {
                log.error("Failed to enqueue notification: {}", notification.getId(), e);
                notificationCommandService.markFailed(notification.getId(), "Failed to enqueue notification: " + e.getMessage());
                failedCount++;
            }
        }

        return new DispatchResult(dispatchedCount, failedCount);
    }
}
