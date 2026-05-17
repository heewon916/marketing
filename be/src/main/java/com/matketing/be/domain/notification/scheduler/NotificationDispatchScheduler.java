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

    // 기존: 매 1분 실행 (로컬 및 운영)
    // @Scheduled(cron = "0 * * * * *", zone = "Asia/Seoul")
    
    // 변경: 매 5분 실행 (로그 축소 및 리소스 최적화)
    @Scheduled(cron = "0 */5 * * * *", zone = "Asia/Seoul")
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
