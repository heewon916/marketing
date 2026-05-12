package com.matketing.be.domain.analytic.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.matketing.be.domain.analytic.entity.AccountWeeklyMetric;

import java.time.LocalDate;
import java.util.Optional;
import java.util.UUID;

public interface AccountWeeklyMetricRepository extends JpaRepository<AccountWeeklyMetric, UUID> {

    /**
     * 가게 ID와 주차 시작일 기준으로 삭제되지 않은 주간 통계 데이터를 조회한다.
     */
    @Query("""
                select awm
                from AccountWeeklyMetric awm
                where awm.store.id = :storeId
                  and awm.weekStart = :weekStart
                  and (awm.isDeleted = false or awm.isDeleted is null)
            """)
    Optional<AccountWeeklyMetric> findActiveByStoreIdAndWeekStart(
            @Param("storeId") UUID storeId,
            @Param("weekStart") LocalDate weekStart);
}
