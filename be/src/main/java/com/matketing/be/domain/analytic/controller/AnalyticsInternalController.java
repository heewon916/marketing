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

    @Operation(summary = "주간 콘텐츠 분석 및 저장", description = "수집된 instagram_metrics와 contents 데이터를 기반으로 지난주 주간 통계를 집계해 account_weekly_metrics에 저장합니다. 사용자 직접 호출용 API가 아닙니다.")
    @PostMapping("/weekly-analysis")
    public ResponseEntity<WeeklyAggregationResult> runWeeklyAnalysis() {
        WeeklyAggregationResult result = analyticsAggregationService.aggregateLastWeek();
        return ResponseEntity.ok(result);
    }
}
