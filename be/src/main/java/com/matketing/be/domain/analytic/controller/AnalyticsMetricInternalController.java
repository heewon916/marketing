package com.matketing.be.domain.analytic.controller;

import com.matketing.be.domain.analytic.dto.WeeklyMetricCollectResult;
import com.matketing.be.domain.analytic.service.AnalyticsMetricCollectService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.time.LocalDate;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/internal/metrics")
@RequiredArgsConstructor
@Tag(name = "Analytics Internal", description = "내부 배치용 Meta 통계 수집 API")
public class AnalyticsMetricInternalController {

    private final AnalyticsMetricCollectService analyticsMetricCollectService;

    @Operation(
            summary = "주간 Meta 데이터 수집",
            description = "Instagram User Insights API로 주간 계정 단위 지표를 수집해 account_weekly_metrics에 저장합니다. week_start를 생략하면 지난주 월요일 기준으로 수집하고, 전달하면 해당 주차 기준으로 재수집합니다. 내부 테스트/재수집용이며 사용자 직접 호출용 API가 아닙니다."
    )
    @PostMapping("/collect")
    public ResponseEntity<WeeklyMetricCollectResult> collectWeeklyMetrics(
            @Parameter(description = "수집할 주차의 시작일. 생략 시 Asia/Seoul 기준 지난주 월요일을 사용한다.", example = "2026-05-11")
            @RequestParam(value = "week_start", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate weekStart
    ) {
        WeeklyMetricCollectResult result = analyticsMetricCollectService.collect(weekStart);
        return ResponseEntity.ok(result);
    }
}
