package com.matketing.be.domain.analytic.controller;

import com.matketing.be.domain.analytic.dto.WeeklyAggregationResult;
import com.matketing.be.domain.analytic.service.AnalyticsAggregationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/internal/stats")
@RequiredArgsConstructor
@Tag(name = "Analytics Internal", description = "내부 배치용 통계 집계 API")
public class AnalyticsInternalController {

    private final AnalyticsAggregationService analyticsAggregationService;

    @Operation(
            summary = "주간 instagram_metrics 기반 집계",
            description = "instagram_metrics와 contents 데이터를 기반으로 지난주 통계를 account_weekly_metrics에 집계합니다. 현재 운영/시연 수집 흐름은 /api/v1/internal/metrics/collect입니다. metrics/collect 이후 이 API를 호출하면 account_weekly_metrics 값이 덮일 수 있으며, 대상 주차 instagram_metrics가 비어 있는 store는 기존 값을 0으로 덮지 않고 skip합니다."
    )
    @PostMapping("/weekly-analysis")
    public ResponseEntity<WeeklyAggregationResult> runWeeklyAnalysis() {
        WeeklyAggregationResult result = analyticsAggregationService.aggregateLastWeek();
        return ResponseEntity.ok(result);
    }
}
