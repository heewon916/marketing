package com.matketing.be.domain.analytic.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDate;

public record WeeklyAggregationResult(
        @JsonProperty("week_start") LocalDate weekStart,
        @JsonProperty("week_end") LocalDate weekEnd,
        @JsonProperty("analyzed_stores") int analyzedStores,
        @JsonProperty("skipped_stores") int skippedStores) {
}
