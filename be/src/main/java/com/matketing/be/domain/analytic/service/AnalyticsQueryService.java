package com.matketing.be.domain.analytic.service;

import com.matketing.be.domain.analytic.dto.AchievementResponse;
import com.matketing.be.domain.analytic.dto.ReachResponse;
import com.matketing.be.domain.analytic.dto.VisitIntentResponse;
import com.matketing.be.domain.analytic.repository.AccountWeeklyMetricRepository;
import com.matketing.be.domain.content.repository.ContentRepository;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
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
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AnalyticsQueryService {

    private final AccountWeeklyMetricRepository accountWeeklyMetricRepository;
    private final StoreRepository storeRepository;
    private final ContentRepository contentRepository;

    private static final ZoneId SEOUL_ZONE = ZoneId.of("Asia/Seoul");

    /**
     * null 안전을 위한 Integer 변환 헬퍼 메서드
     */
    private int nvl(Integer value) {
        return value == null ? 0 : value;
    }

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
     * 주차 시작일 기준 주차 종료일을 계산한다.
     */
    private LocalDate getWeekEnd(LocalDate weekStart) {
        return weekStart.plusDays(6);
    }



    /**
     * 사용자 ID 기준으로 매장을 조회한다.
     */
    private Store findStoreByUserId(UUID userId) {
        return storeRepository.findFirstByUserId(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.STORE_NOT_FOUND));
    }

    /**
     * 주어진 사용자와 주차 기준으로 주간 가게 노출 수를 조회한다.
     * 통계 데이터가 없으면 totalReach를 0으로 응답한다.
     */
    public ReachResponse getReach(UUID userId) {
        Store store = findStoreByUserId(userId);

        LocalDate targetWeekStart = getLastWeekStart();
        LocalDate targetWeekEnd = getWeekEnd(targetWeekStart);

        return accountWeeklyMetricRepository.findActiveByStoreIdAndWeekStart(store.getId(), targetWeekStart)
                .map(awm -> new ReachResponse(targetWeekStart, targetWeekEnd, nvl(awm.getTotalReach())))
                .orElseGet(() -> {
                    log.info("주간 노출 수 통계 데이터 없음. 기본값 0 반환. storeId={}, targetWeekStart={}", store.getId(), targetWeekStart);
                    return new ReachResponse(targetWeekStart, targetWeekEnd, 0);
                });
    }

    /**
     * 주간 실질 방문 의사 지수를 조회한다.
     * 저장 수와 공유 수를 도달 수로 나누어 소수점 둘째 자리까지 계산한다.
     */
    public VisitIntentResponse getVisitIntent(UUID userId) {
        Store store = findStoreByUserId(userId);

        LocalDate targetWeekStart = getLastWeekStart();
        LocalDate targetWeekEnd = getWeekEnd(targetWeekStart);

        return accountWeeklyMetricRepository.findActiveByStoreIdAndWeekStart(store.getId(), targetWeekStart)
                .map(awm -> {
                    int reach = nvl(awm.getTotalReach());
                    int saves = nvl(awm.getTotalSaves());
                    int shares = nvl(awm.getTotalShares());

                    BigDecimal score = BigDecimal.ZERO;
                    if (reach > 0) {
                        score = new BigDecimal(saves + shares)
                                .divide(new BigDecimal(reach), 4, RoundingMode.HALF_UP)
                                .multiply(new BigDecimal(100))
                                .setScale(2, RoundingMode.HALF_UP);
                    }

                    return new VisitIntentResponse(
                            targetWeekStart,
                            targetWeekEnd,
                            score,
                            new VisitIntentResponse.Breakdown(reach, saves, shares));
                })
                .orElseGet(() -> {
                    log.info("주간 방문 의사 지수 통계 데이터 없음. 기본값 0 반환. storeId={}, targetWeekStart={}", store.getId(), targetWeekStart);
                    return new VisitIntentResponse(
                            targetWeekStart,
                            targetWeekEnd,
                            BigDecimal.ZERO,
                            new VisitIntentResponse.Breakdown(0, 0, 0));
                });
    }

    /**
     * 주간 포스팅 달성률을 조회한다.
     * 실제 발행 게시물 수와 목표 게시물 수를 기준으로 계산한다.
     */
    public AchievementResponse getAchievement(UUID userId) {
        Store store = findStoreByUserId(userId);

        LocalDate targetWeekStart = getThisWeekStart();
        LocalDate targetWeekEnd = getWeekEnd(targetWeekStart);

        // TODO: 목표 게시물 수 설정 기능 확정 후 고정값 4 대신 DB 설정값으로 교체 필요
        int targetCount = 4;

        OffsetDateTime startAt = targetWeekStart.atStartOfDay(SEOUL_ZONE).toOffsetDateTime();
        OffsetDateTime endAt = targetWeekStart.plusWeeks(1).atStartOfDay(SEOUL_ZONE).toOffsetDateTime();

        long actualPostCountLong = contentRepository.countPublishedContentsByStoreAndPeriod(store.getId(), startAt, endAt);
        int actualCount = (int) actualPostCountLong;

        BigDecimal rate = BigDecimal.ZERO;
        if (targetCount > 0) {
            rate = new BigDecimal(actualCount)
                    .divide(new BigDecimal(targetCount), 4, RoundingMode.HALF_UP)
                    .multiply(new BigDecimal(100))
                    .setScale(2, RoundingMode.HALF_UP);
        }

        return new AchievementResponse(targetWeekStart, targetWeekEnd, targetCount, actualCount, rate);
    }
}
