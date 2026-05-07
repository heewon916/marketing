package com.matketing.be.domain.notification.scheduler;

import com.matketing.be.domain.notification.dto.DispatchResult;
import com.matketing.be.domain.notification.service.NotificationDispatchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class NotificationDispatchScheduler {

    private final NotificationDispatchService notificationDispatchService;

    // 로컬 테스트용 cron: @Scheduled(cron = "0 * * * * *", zone = "Asia/Seoul") // 매분, 운영에서도 사용
    @Scheduled(cron = "0 * * * * *", zone = "Asia/Seoul")
    public void dispatchDueNotifications() {
        try {
            log.info("[NotificationDispatchScheduler] Starting to dispatch due notifications...");
            DispatchResult result = notificationDispatchService.dispatchDueNotifications(100);
            log.info("[NotificationDispatchScheduler] Dispatch scheduler completed. dispatchedCount={}, failedCount={}",
                    result.getDispatchedCount(), result.getFailedCount());
        } catch (Exception e) {
            log.error("[NotificationDispatchScheduler] Failed to dispatch due notifications", e);
        }
    }
}
