package com.matketing.be.domain.analytic.service;

import com.matketing.be.domain.analytic.dto.AchievementResponse;
import com.matketing.be.domain.analytic.dto.ReachResponse;
import com.matketing.be.domain.analytic.dto.VisitIntentResponse;
import com.matketing.be.domain.analytic.entity.AccountWeeklyMetric;
import com.matketing.be.domain.analytic.repository.AccountWeeklyMetricRepository;
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
import java.time.LocalDate;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AnalyticsQueryService {

    private final AccountWeeklyMetricRepository accountWeeklyMetricRepository;
    private final StoreRepository storeRepository;

    /**
     * null 안전을 위한 Integer 변환 헬퍼 메서드
     */
    private int nvl(Integer value) {
        return value == null ? 0 : value;
    }

    /**
     * 주어진 사용자와 주차 기준으로 주간 가게 노출 수를 조회한다.
     * 통계 데이터가 없으면 totalReach를 0으로 응답한다.
     */
    public ReachResponse getReach(UUID userId, LocalDate weekStart) {
        Store store = storeRepository.findFirstByUserId(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.STORE_NOT_FOUND));

        return accountWeeklyMetricRepository.findActiveByStoreIdAndWeekStart(store.getId(), weekStart)
                .map(awm -> new ReachResponse(weekStart, nvl(awm.getTotalReach())))
                .orElseGet(() -> {
                    log.info("주간 노출 수 통계 데이터 없음. 기본값 0 반환. storeId={}, weekStart={}", store.getId(), weekStart);
                    return new ReachResponse(weekStart, 0);
                });
    }

    /**
     * 주간 실질 방문 의사 지수를 조회한다.
     * 저장 수와 공유 수를 도달 수로 나누어 소수점 둘째 자리까지 계산한다.
     */
    public VisitIntentResponse getVisitIntent(UUID userId, LocalDate weekStart) {
        Store store = storeRepository.findFirstByUserId(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.STORE_NOT_FOUND));

        return accountWeeklyMetricRepository.findActiveByStoreIdAndWeekStart(store.getId(), weekStart)
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
                            weekStart,
                            score,
                            new VisitIntentResponse.Breakdown(reach, saves, shares));
                })
                .orElseGet(() -> {
                    log.info("주간 방문 의사 지수 통계 데이터 없음. 기본값 0 반환. storeId={}, weekStart={}", store.getId(), weekStart);
                    return new VisitIntentResponse(
                            weekStart,
                            BigDecimal.ZERO,
                            new VisitIntentResponse.Breakdown(0, 0, 0));
                });
    }

    /**
     * 주간 포스팅 달성률을 조회한다.
     * 실제 발행 게시물 수와 목표 게시물 수를 기준으로 계산한다.
     */
    public AchievementResponse getAchievement(UUID userId, LocalDate weekStart) {
        Store store = storeRepository.findFirstByUserId(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.STORE_NOT_FOUND));

        return accountWeeklyMetricRepository.findActiveByStoreIdAndWeekStart(store.getId(), weekStart)
                .map(awm -> {
                    int targetCount = nvl(awm.getTargetPostCount());
                    int actualCount = nvl(awm.getActualPostCount());

                    BigDecimal rate = BigDecimal.ZERO;
                    if (awm.getAchievementRate() != null) {
                        rate = awm.getAchievementRate().setScale(2, RoundingMode.HALF_UP);
                    } else if (targetCount > 0) {
                        rate = new BigDecimal(actualCount)
                                .divide(new BigDecimal(targetCount), 4, RoundingMode.HALF_UP)
                                .multiply(new BigDecimal(100))
                                .setScale(2, RoundingMode.HALF_UP);
                    }

                    return new AchievementResponse(weekStart, targetCount, actualCount, rate);
                })
                .orElseGet(() -> {
                    log.info("주간 포스팅 달성률 통계 데이터 없음. 기본값 0 반환. storeId={}, weekStart={}", store.getId(), weekStart);
                    return new AchievementResponse(weekStart, 0, 0, BigDecimal.ZERO);
                });
    }
}
