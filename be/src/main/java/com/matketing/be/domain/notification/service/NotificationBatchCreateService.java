package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.dto.NotificationBatchCreateResponse;
import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.domain.notification.enums.NotificationType;
import com.matketing.be.domain.notification.repository.NotificationRepository;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationBatchCreateService {

    private final NotificationCommandService notificationCommandService;
    private final NotificationMessageResolver notificationMessageResolver;
    private final NotificationRepository notificationRepository;
    private final StoreRepository storeRepository;

    private LocalTime getInstagramBestPostTime(DayOfWeek dayOfWeek) {
        switch (dayOfWeek) {
            case MONDAY: return LocalTime.of(19, 0);
            case TUESDAY: return LocalTime.of(19, 0);
            case WEDNESDAY: return LocalTime.of(12, 0);
            case THURSDAY: return LocalTime.of(9, 0);
            case FRIDAY: return LocalTime.of(22, 0);
            case SATURDAY: return LocalTime.of(21, 0);
            case SUNDAY: return LocalTime.of(21, 0);
            default: return LocalTime.of(19, 0);
        }
    }

    public NotificationBatchCreateResponse createBatch(NotificationType type) {
        if (type != NotificationType.REMIND && type != NotificationType.WEATHER_MENU &&
            type != NotificationType.HOLIDAY_MENU && type != NotificationType.HOLIDAY_OPERATION &&
            type != NotificationType.WEEKLY_STATS && type != NotificationType.POST_PROMOTION_REMINDER) {
            throw new BusinessException(ErrorCode.INVALID_NOTIFICATION_BATCH_TYPE);
        }

        ZoneId zoneId = ZoneId.of("Asia/Seoul");
        LocalDate today = LocalDate.now(zoneId);
        OffsetDateTime startOfDay = today.atStartOfDay(zoneId).toOffsetDateTime();
        OffsetDateTime endOfDay = today.plusDays(1).atStartOfDay(zoneId).toOffsetDateTime();

        // TODO: REMIND는 매장별 영업 종료 시간 기준으로 생성하도록 변경
        // TODO: WEATHER_MENU는 날씨 API 및 메뉴 매칭 연동 후 생성하도록 변경
        // TODO: HOLIDAY_MENU/HOLIDAY_OPERATION은 공휴일 데이터 연동 후 생성하도록 변경
        // TODO: WEEKLY_STATS는 게시글 통계 데이터 연동 후 생성하도록 변경
        log.info("[NotificationBatchCreateService] Start creating {} batch", type);

        List<Store> stores = storeRepository.findAll();
        
        log.info("[NotificationBatchCreateService] targetStoreCount={}", stores.size());

        int createdCount = 0;
        int skippedCount = 0;

        for (Store store : stores) {
            try {
                UUID storeId = store.getId();

                // notification 저장 전에 반드시 stores 테이블에 존재하는지 검증
                if (!storeRepository.existsById(storeId)) {
                    log.warn("[NotificationBatchCreateService] Store does not exist. Skipping notification. storeId={}", storeId);
                    continue;
                }

                boolean exists = notificationRepository.existsByStoreIdAndTypeAndScheduledAtBetween(
                        storeId, type, startOfDay, endOfDay
                );

                if (exists) {
                    skippedCount++;
                    log.info("[NotificationBatchCreateService] Skipped duplicate. type={}, storeId={}, date={}, scheduledAt=N/A", type, storeId, today);
                } else {
                    OffsetDateTime scheduledAt;
                    switch (type) {
                        case REMIND:
                            scheduledAt = today.atTime(9, 0).atZone(zoneId).toOffsetDateTime();
                            break;
                        case WEATHER_MENU:
                            scheduledAt = today.atTime(10, 0).atZone(zoneId).toOffsetDateTime();
                            break;
                        case HOLIDAY_MENU:
                            scheduledAt = today.atTime(11, 0).atZone(zoneId).toOffsetDateTime();
                            break;
                        case HOLIDAY_OPERATION:
                            scheduledAt = today.atTime(12, 0).atZone(zoneId).toOffsetDateTime();
                            break;
                        case WEEKLY_STATS:
                            scheduledAt = today.atTime(13, 0).atZone(zoneId).toOffsetDateTime();
                            break;
                        case POST_PROMOTION_REMINDER:
                            LocalTime bestTime = getInstagramBestPostTime(today.getDayOfWeek());
                            scheduledAt = ZonedDateTime.of(today, bestTime, zoneId).toOffsetDateTime();
                            log.info("[NotificationBatchCreateService] today={}, dayOfWeek={}, scheduledAt={}", today, today.getDayOfWeek(), scheduledAt);
                            break;
                        default:
                            scheduledAt = OffsetDateTime.now();
                    }

                    String notificationText = notificationMessageResolver.resolveNotificationText(type);
                    String webUrl = notificationMessageResolver.resolveWebUrl(type, null);

                    Notification created = notificationCommandService.createPendingNotification(
                            storeId,
                            type,
                            notificationText,
                            scheduledAt,
                            webUrl,
                            null
                    );
                    log.info("[NotificationBatchCreateService] Created successfully. type={}, storeId={}, notificationId={}, scheduledAt={}", type, storeId, created.getId(), scheduledAt);
                    createdCount++;
                }
            } catch (Exception e) {
                log.warn("[NotificationBatchCreateService] Failed to create notification. type={}, storeId={}, scheduledAt=N/A, message={}", type, store.getId(), e.getMessage());
            }
        }

        return new NotificationBatchCreateResponse(createdCount, skippedCount);
    }
}
