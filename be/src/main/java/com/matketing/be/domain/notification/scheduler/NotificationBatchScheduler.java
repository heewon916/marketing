package com.matketing.be.domain.notification.scheduler;

import com.matketing.be.domain.notification.dto.NotificationBatchCreateResponse;
import com.matketing.be.domain.notification.enums.NotificationType;
import com.matketing.be.domain.notification.service.NotificationBatchCreateService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class NotificationBatchScheduler {

    private final NotificationBatchCreateService notificationBatchCreateService;

    // 로컬 테스트 시 매분 실행으로 임시 변경 가능: @Scheduled(cron = "0 * * * * *", zone = "Asia/Seoul")
    @Scheduled(cron = "0 0 0 * * *", zone = "Asia/Seoul")
    public void createDailyNotificationBatches() {
        log.info("[NotificationBatchScheduler] Starting to create daily notification batches...");
        NotificationType[] dailyTypes = {
                NotificationType.REMIND,
                NotificationType.WEATHER_MENU,
                NotificationType.HOLIDAY_MENU,
                NotificationType.HOLIDAY_OPERATION
        };

        for (NotificationType type : dailyTypes) {
            try {
                NotificationBatchCreateResponse response = notificationBatchCreateService.createBatch(type);
                log.info("[NotificationBatchScheduler] Daily batch created for {}. createdCount={}, skippedCount={}",
                        type, response.getCreatedCount(), response.getSkippedCount());
            } catch (Exception e) {
                log.error("[NotificationBatchScheduler] Failed to create daily batch for {}", type, e);
            }
        }
    }

    // 로컬 테스트 시 매분 실행으로 임시 변경 가능: @Scheduled(cron = "0 * * * * *", zone = "Asia/Seoul")
    @Scheduled(cron = "0 0 0 * * SUN", zone = "Asia/Seoul")
    public void createWeeklyNotificationBatches() {
        log.info("[NotificationBatchScheduler] Starting to create weekly notification batches...");
        try {
            NotificationBatchCreateResponse response = notificationBatchCreateService.createBatch(NotificationType.WEEKLY_STATS);
            log.info("[NotificationBatchScheduler] Weekly batch created for WEEKLY_STATS. createdCount={}, skippedCount={}",
                    response.getCreatedCount(), response.getSkippedCount());
        } catch (Exception e) {
            log.error("[NotificationBatchScheduler] Failed to create weekly batch for WEEKLY_STATS", e);
        }
    }
}
