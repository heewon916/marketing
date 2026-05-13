package com.matketing.be.domain.analytic.service;

import com.matketing.be.domain.analytic.client.MetaUserInsightsClient;
import com.matketing.be.domain.analytic.dto.MetaUserInsightsResult;
import com.matketing.be.domain.analytic.dto.WeeklyMetricCollectResult;
import com.matketing.be.domain.analytic.entity.AccountWeeklyMetric;
import com.matketing.be.domain.analytic.repository.AccountWeeklyMetricRepository;
import com.matketing.be.domain.content.repository.ContentRepository;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.domain.user.entity.User;
import com.matketing.be.domain.user.repository.UserRepository;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.temporal.TemporalAdjusters;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

@Slf4j
@Service
@RequiredArgsConstructor
public class AnalyticsMetricCollectService {

    private static final ZoneId SEOUL_ZONE = ZoneId.of("Asia/Seoul");
    // TODO: 목표 게시물 수 설정 기능 확정 후 고정값 4 대신 DB 설정값으로 교체 필요
    private static final int TEMP_TARGET_POST_COUNT = 4;

    private final StoreRepository storeRepository;
    private final UserRepository userRepository;
    private final AccountWeeklyMetricRepository accountWeeklyMetricRepository;
    private final ContentRepository contentRepository;
    private final MetaUserInsightsClient metaUserInsightsClient;
    private final PlatformTransactionManager transactionManager;

    /**
     * Instagram User Insights API로 지난주 store별 계정 단위 지표를 수집하여 account_weekly_metrics에 저장한다.
     */
    @Transactional(readOnly = true)
    public WeeklyMetricCollectResult collectLastWeek() {
        LocalDate lastWeekStart = getLastWeekStart();
        LocalDate weekEndExclusiveDate = lastWeekStart.plusWeeks(1);
        OffsetDateTime weekStartAt = toStartOfDay(lastWeekStart);
        OffsetDateTime weekEndExclusiveAt = toStartOfDay(weekEndExclusiveDate);

        int collectedStores = 0;
        int skippedStores = 0;
        int failedStores = 0;

        List<Store> stores = storeRepository.findAll();
        for (Store store : stores) {
            try {
                Optional<User> userOptional = findCollectableUser(store, weekEndExclusiveAt, lastWeekStart);
                if (userOptional.isEmpty()) {
                    skippedStores++;
                    continue;
                }

                OffsetDateTime effectiveStartAt = resolveEffectiveStartAt(store, weekStartAt);
                if (!effectiveStartAt.equals(weekStartAt)) {
                    log.info("Apply partial-week collection start. storeId={}, weekStart={}, effectiveStartAt={}",
                            store.getId(), lastWeekStart, effectiveStartAt);
                }

                User user = userOptional.get();
                MetaUserInsightsResult insights = metaUserInsightsClient.fetchUserInsights(
                        user.getInstagramUserId(),
                        user.getAccessToken(),
                        toEpochSecond(effectiveStartAt),
                        toEpochSecond(weekEndExclusiveAt)
                );

                // TODO: 현재 totalReach는 Meta User Insights의 views metric을 매핑한다.
                // 추후 고유 도달 수가 필요하면 reach metric 또는 totalViews 필드명으로 전환 검토.
                int totalReach = insights.views();
                int totalSaves = insights.saves();
                int totalShares = insights.shares();

                long actualPostCountLong = contentRepository.countPublishedContentsByStoreAndPeriod(
                        store.getId(), effectiveStartAt, weekEndExclusiveAt);
                int actualPostCount = (int) actualPostCountLong;

                BigDecimal visitIntentScore = calculateRate(totalSaves + totalShares, totalReach);
                BigDecimal achievementRate = calculateRate(actualPostCount, TEMP_TARGET_POST_COUNT);

                upsertMetric(store.getId(), lastWeekStart, totalReach, totalSaves, totalShares,
                        actualPostCount, achievementRate, visitIntentScore);
                collectedStores++;
            } catch (Exception exception) {
                failedStores++;
                log.warn("meta weekly metrics collection failed. storeId={}, weekStart={}, message={}",
                        store.getId(), lastWeekStart, exception.getMessage(), exception);
            }
        }

        return new WeeklyMetricCollectResult(
                lastWeekStart,
                lastWeekStart.plusDays(6),
                collectedStores,
                skippedStores,
                failedStores
        );
    }

    private Optional<User> findCollectableUser(Store store, OffsetDateTime weekEndExclusiveAt, LocalDate weekStart) {
        if (store.getCreatedAt() != null && !store.getCreatedAt().isBefore(weekEndExclusiveAt)) {
            log.info("Skip metrics collection for store created after target week. storeId={}, createdAt={}, weekStart={}",
                    store.getId(), store.getCreatedAt(), weekStart);
            return Optional.empty();
        }
        if (store.getUserId() == null) {
            log.info("Skip metrics collection because store userId is missing. storeId={}, weekStart={}",
                    store.getId(), weekStart);
            return Optional.empty();
        }

        Optional<User> userOptional = userRepository.findById(store.getUserId());
        if (userOptional.isEmpty()) {
            log.info("Skip metrics collection because user was not found. storeId={}, userId={}, weekStart={}",
                    store.getId(), store.getUserId(), weekStart);
            return Optional.empty();
        }

        User user = userOptional.get();
        if (isBlank(user.getInstagramUserId())) {
            log.info("Skip metrics collection because instagramUserId is missing. storeId={}, userId={}, weekStart={}",
                    store.getId(), store.getUserId(), weekStart);
            return Optional.empty();
        }
        if (isBlank(user.getAccessToken())) {
            log.info("Skip metrics collection because accessToken is missing. storeId={}, userId={}, weekStart={}",
                    store.getId(), store.getUserId(), weekStart);
            return Optional.empty();
        }

        return Optional.of(user);
    }

    private OffsetDateTime resolveEffectiveStartAt(Store store, OffsetDateTime weekStartAt) {
        if (store.getCreatedAt() != null && store.getCreatedAt().isAfter(weekStartAt)) {
            return store.getCreatedAt();
        }
        return weekStartAt;
    }

    private void upsertMetric(
            java.util.UUID storeId,
            LocalDate weekStart,
            int totalReach,
            int totalSaves,
            int totalShares,
            int actualPostCount,
            BigDecimal achievementRate,
            BigDecimal visitIntentScore
    ) {
        TransactionTemplate transactionTemplate = new TransactionTemplate(transactionManager);
        transactionTemplate.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRES_NEW);
        transactionTemplate.executeWithoutResult(status -> accountWeeklyMetricRepository
                .findActiveByStoreIdAndWeekStart(storeId, weekStart)
                .ifPresentOrElse(
                        existingMetric -> existingMetric.updateMetrics(
                                totalReach, totalSaves, totalShares,
                                TEMP_TARGET_POST_COUNT, actualPostCount,
                                achievementRate, visitIntentScore),
                        () -> {
                            Store storeReference = storeRepository.getReferenceById(storeId);
                            AccountWeeklyMetric newMetric = AccountWeeklyMetric.create(
                                    storeReference, weekStart,
                                    totalReach, totalSaves, totalShares,
                                    TEMP_TARGET_POST_COUNT, actualPostCount,
                                    achievementRate, visitIntentScore);
                            accountWeeklyMetricRepository.save(newMetric);
                        }));
    }

    private BigDecimal calculateRate(int numerator, int denominator) {
        if (denominator <= 0) {
            return BigDecimal.ZERO;
        }
        return new BigDecimal(numerator)
                .divide(new BigDecimal(denominator), 4, RoundingMode.HALF_UP)
                .multiply(new BigDecimal(100))
                .setScale(2, RoundingMode.HALF_UP);
    }

    private LocalDate getThisWeekStart() {
        return LocalDate.now(SEOUL_ZONE)
                .with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
    }

    private LocalDate getLastWeekStart() {
        return getThisWeekStart().minusWeeks(1);
    }

    private OffsetDateTime toStartOfDay(LocalDate date) {
        return date.atStartOfDay(SEOUL_ZONE).toOffsetDateTime();
    }

    private long toEpochSecond(OffsetDateTime dateTime) {
        return dateTime.toEpochSecond();
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }
}
