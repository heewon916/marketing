package com.matketing.be.domain.analytic.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.matketing.be.domain.analytic.entity.InstagramMetric;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public interface InstagramMetricRepository extends JpaRepository<InstagramMetric, UUID> {

    /**
     * 가게 ID와 주차 시작일 기준으로 게시물별 인스타그램 지표를 조회한다.
     */
    List<InstagramMetric> findByStore_IdAndWeekStart(UUID storeId, LocalDate weekStart);
}
