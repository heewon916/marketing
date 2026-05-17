package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.dto.NotificationBatchCreateResponse;
import com.matketing.be.domain.notification.enums.NotificationType;
import com.matketing.be.domain.notification.repository.NotificationRepository;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
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

    public NotificationBatchCreateResponse createBatch(NotificationType type) {
        if (type != NotificationType.REMIND && type != NotificationType.WEATHER_MENU &&
            type != NotificationType.HOLIDAY_MENU && type != NotificationType.HOLIDAY_OPERATION &&
            type != NotificationType.WEEKLY_STATS) {
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
        List<Store> stores = storeRepository.findAll();

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
                } else {
                    // TODO: 실제 배치에서는 type별 정책에 맞춰 scheduledAt 계산하도록 변경
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
                        default:
                            scheduledAt = OffsetDateTime.now();
                    }

                    String notificationText = notificationMessageResolver.resolveNotificationText(type);
                    String webUrl = notificationMessageResolver.resolveWebUrl(type, null);

                    notificationCommandService.createPendingNotification(
                            storeId,
                            type,
                            notificationText,
                            scheduledAt,
                            webUrl,
                            null
                    );
                    createdCount++;
                }
            } catch (Exception e) {
                log.warn("[NotificationBatchCreateService] Failed to create notification. type={}, storeId={}", type, store.getId(), e);
            }
        }

        return new NotificationBatchCreateResponse(createdCount, skippedCount);
    }
}
