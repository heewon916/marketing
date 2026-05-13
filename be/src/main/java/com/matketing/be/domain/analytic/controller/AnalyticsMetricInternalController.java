package com.matketing.be.domain.analytic.controller;

import com.matketing.be.domain.analytic.dto.WeeklyMetricCollectResult;
import com.matketing.be.domain.analytic.service.AnalyticsMetricCollectService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/internal/metrics")
@RequiredArgsConstructor
@Tag(name = "Analytics Internal", description = "내부 배치용 Meta 통계 수집 API")
public class AnalyticsMetricInternalController {

    private final AnalyticsMetricCollectService analyticsMetricCollectService;

    @Operation(
            summary = "주간 Meta 데이터 수집",
            description = "현재 운영/시연용 수집 API입니다. Instagram User Insights API로 지난주 월~일 기준 계정 단위 지표 views, saves, shares를 수집해 account_weekly_metrics에 직접 저장합니다. instagram_metrics에는 저장하지 않습니다."
    )
    @PostMapping("/collect")
    public ResponseEntity<WeeklyMetricCollectResult> collectWeeklyMetrics() {
        WeeklyMetricCollectResult result = analyticsMetricCollectService.collectLastWeek();
        return ResponseEntity.ok(result);
    }
}
