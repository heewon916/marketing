package com.matketing.be.domain.analytic.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDate;

public record WeeklyMetricCollectResult(
        @JsonProperty("week_start") LocalDate weekStart,
        @JsonProperty("week_end") LocalDate weekEnd,
        @JsonProperty("collected_stores") int collectedStores,
        @JsonProperty("skipped_stores") int skippedStores,
        @JsonProperty("failed_stores") int failedStores) {
}
