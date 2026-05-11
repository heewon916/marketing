package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.entity.DeviceToken;
import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.domain.notification.enums.NotificationStatus;
import com.matketing.be.domain.notification.repository.DeviceTokenRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationWorker {

    private final NotificationQueueService notificationQueueService;
    private final NotificationQueryService notificationQueryService;
    private final NotificationCommandService notificationCommandService;
    private final DeviceTokenRepository deviceTokenRepository;
    private final FcmPushService fcmPushService;

    // 주기적으로 Redis Queue에서 알림을 꺼내 FCM 발송을 처리한다.
    @Scheduled(fixedDelay = 1000)
    public void processQueue() {
        try {
            Optional<UUID> notificationIdOpt = notificationQueueService.dequeue();
            if (notificationIdOpt.isEmpty()) {
                return;
            }

            UUID id = notificationIdOpt.get();
            Notification notification;
            try {
                notification = notificationQueryService.getById(id);
            } catch (Exception e) {
                log.error("Notification not found for id: {}", id, e);
                return;
            }

            if (notification.getStatus() == NotificationStatus.SENT || notification.getStatus() == NotificationStatus.FAILED) {
                log.debug("Notification {} is already in terminal state: {}", id, notification.getStatus());
                return;
            }

            String title = NotificationTitleResolver.resolve(notification.getType());
            String body = notification.getNotification();
            String webUrl = notification.getWebUrl();

            // TODO: 추후 store_id -> store owner user_id 조회로 교체
            UUID userId = UUID.fromString("00000000-0000-0000-0000-000000000000");

            List<DeviceToken> tokens = deviceTokenRepository.findByUserIdAndIsActiveTrue(userId);
            if (tokens == null || tokens.isEmpty()) {
                notificationCommandService.markFailed(id, "No active device tokens");
                return;
            }

            int[] results = fcmPushService.sendPushNotification(tokens, title, body, webUrl);
            int sentCount = results[0];

            if (sentCount > 0) {
                notificationCommandService.markSent(id);
            } else {
                notificationCommandService.increaseRetryCount(id);
                notificationCommandService.markFailed(id, "Failed to send FCM notification");
            }

        } catch (Exception e) {
            log.error("Unexpected error in NotificationWorker", e);
        }
    }
}
