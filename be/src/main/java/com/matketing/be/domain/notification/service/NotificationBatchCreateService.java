package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.dto.NotificationBatchCreateResponse;
import com.matketing.be.domain.notification.enums.NotificationType;
import com.matketing.be.domain.notification.repository.NotificationRepository;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationBatchCreateService {

    private final NotificationCommandService notificationCommandService;
    private final NotificationMessageResolver notificationMessageResolver;
    private final NotificationRepository notificationRepository;

    @Transactional
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

        // TODO: Store 도메인 연동 후 실제 영업 매장 목록을 조회하도록 변경
        // TODO: REMIND는 매장별 영업 종료 시간 기준으로 생성하도록 변경
        // TODO: WEATHER_MENU는 날씨 API 및 메뉴 매칭 연동 후 생성하도록 변경
        // TODO: HOLIDAY_MENU/HOLIDAY_OPERATION은 공휴일 데이터 연동 후 생성하도록 변경
        // TODO: WEEKLY_STATS는 게시글 통계 데이터 연동 후 생성하도록 변경
        UUID storeId = UUID.fromString("00000000-0000-0000-0000-000000000000");

        int createdCount = 0;
        int skippedCount = 0;

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

        return new NotificationBatchCreateResponse(createdCount, skippedCount);
    }
}
