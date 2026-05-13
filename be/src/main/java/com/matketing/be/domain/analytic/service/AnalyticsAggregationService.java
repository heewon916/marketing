package com.matketing.be.domain.analytic.service;

import com.matketing.be.domain.analytic.dto.WeeklyAggregationResult;
import com.matketing.be.domain.analytic.entity.AccountWeeklyMetric;
import com.matketing.be.domain.analytic.entity.InstagramMetric;
import com.matketing.be.domain.analytic.repository.AccountWeeklyMetricRepository;
import com.matketing.be.domain.analytic.repository.InstagramMetricRepository;
import com.matketing.be.domain.content.repository.ContentRepository;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.temporal.TemporalAdjusters;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class AnalyticsAggregationService {

    private final StoreRepository storeRepository;
    private final InstagramMetricRepository instagramMetricRepository;
    private final AccountWeeklyMetricRepository accountWeeklyMetricRepository;
    private final ContentRepository contentRepository;

    private static final ZoneId SEOUL_ZONE = ZoneId.of("Asia/Seoul");
    // TODO: 목표 게시물 수 설정 기능 확정 후 고정값 4 대신 DB 설정값으로 교체 필요
    private static final int TEMP_TARGET_POST_COUNT = 4;

    /**
     * Asia/Seoul 기준 이번 주 월요일 날짜를 계산한다.
     */
    private LocalDate getThisWeekStart() {
        return LocalDate.now(SEOUL_ZONE)
                .with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
    }

    /**
     * Asia/Seoul 기준 지난주 월요일 날짜를 계산한다.
     */
    private LocalDate getLastWeekStart() {
        return getThisWeekStart().minusWeeks(1);
    }

    /**
     * LocalDate 기준 주차 시작 시각을 Asia/Seoul OffsetDateTime으로 변환한다.
     */
    private OffsetDateTime toStartOfDay(LocalDate date) {
        return date.atStartOfDay(SEOUL_ZONE).toOffsetDateTime();
    }

    /**
     * null 안전을 위한 Integer 변환 헬퍼 메서드
     */
    private int nvl(Integer value) {
        return value == null ? 0 : value;
    }

    /**
     * Asia/Seoul 기준 지난주 월~일 데이터를 store별로 집계하여 account_weekly_metrics에 저장한다.
     */
    public WeeklyAggregationResult aggregateLastWeek() {
        LocalDate lastWeekStart = getLastWeekStart();
        LocalDate weekEndExclusiveDate = lastWeekStart.plusWeeks(1);
        OffsetDateTime weekEndExclusiveAt = toStartOfDay(weekEndExclusiveDate);
        OffsetDateTime weekStartAt = toStartOfDay(lastWeekStart);

        List<Store> stores = storeRepository.findAll();
        int analyzedStores = 0;
        int skippedStores = 0;
        // TODO: store별 집계 실패가 전체 배치 롤백으로 이어지지 않도록 트랜잭션 분리 검토 필요
        for (Store store : stores) {
            if (store.getCreatedAt() != null && !store.getCreatedAt().isBefore(weekEndExclusiveAt)) {
                log.info("집계 대상 주차 이후 생성된 store이므로 skip. storeId={}, createdAt={}, weekStart={}",
                        store.getId(), store.getCreatedAt(), lastWeekStart);
                skippedStores++;
                continue;
            }

            OffsetDateTime effectiveStartAt = weekStartAt;
            if (store.getCreatedAt() != null && store.getCreatedAt().isAfter(weekStartAt)) {
                effectiveStartAt = store.getCreatedAt();
            }

            // TODO: Meta 수집 단계에서 store.createdAt 이전 게시물/지표는 수집하지 않도록 필터링 필요
            List<InstagramMetric> metrics = instagramMetricRepository.findByStore_IdAndWeekStart(store.getId(),
                    lastWeekStart);

            int totalReach = 0;
            int totalSaves = 0;
            int totalShares = 0;

            for (InstagramMetric metric : metrics) {
                totalReach += nvl(metric.getReaches());
                totalSaves += nvl(metric.getSaves());
                totalShares += nvl(metric.getShares());
            }

            long actualPostCountLong = contentRepository.countPublishedContentsByStoreAndPeriod(store.getId(),
                    effectiveStartAt, weekEndExclusiveAt);
            int actualPostCount = (int) actualPostCountLong;

            BigDecimal visitIntentScore = BigDecimal.ZERO;
            if (totalReach > 0) {
                visitIntentScore = new BigDecimal(totalSaves + totalShares)
                        .divide(new BigDecimal(totalReach), 4, RoundingMode.HALF_UP)
                        .multiply(new BigDecimal(100))
                        .setScale(2, RoundingMode.HALF_UP);
            }

            BigDecimal achievementRate = BigDecimal.ZERO;
            if (TEMP_TARGET_POST_COUNT > 0) {
                achievementRate = new BigDecimal(actualPostCount)
                        .divide(new BigDecimal(TEMP_TARGET_POST_COUNT), 4, RoundingMode.HALF_UP)
                        .multiply(new BigDecimal(100))
                        .setScale(2, RoundingMode.HALF_UP);
            }

            final int finalTotalReach = totalReach;
            final int finalTotalSaves = totalSaves;
            final int finalTotalShares = totalShares;
            final int finalActualPostCount = actualPostCount;
            final BigDecimal finalAchievementRate = achievementRate;
            final BigDecimal finalVisitIntentScore = visitIntentScore;

            accountWeeklyMetricRepository.findActiveByStoreIdAndWeekStart(store.getId(), lastWeekStart)
                    .ifPresentOrElse(
                            existingMetric -> {
                                existingMetric.updateMetrics(
                                        finalTotalReach, finalTotalSaves, finalTotalShares,
                                        TEMP_TARGET_POST_COUNT, finalActualPostCount,
                                        finalAchievementRate, finalVisitIntentScore);
                            },
                            () -> {
                                AccountWeeklyMetric newMetric = AccountWeeklyMetric.create(
                                        store, lastWeekStart,
                                        finalTotalReach, finalTotalSaves, finalTotalShares,
                                        TEMP_TARGET_POST_COUNT, finalActualPostCount,
                                        finalAchievementRate, finalVisitIntentScore);
                                accountWeeklyMetricRepository.save(newMetric);
                            });

            analyzedStores++;
        }

        return new WeeklyAggregationResult(lastWeekStart, lastWeekStart.plusDays(6), analyzedStores, skippedStores);
    }
}
