package com.matketing.be.domain.analytic.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDate;

public record ReachResponse(
        @JsonProperty("week_start") LocalDate weekStart,
        @JsonProperty("week_end") LocalDate weekEnd,
        @JsonProperty("total_reach") Integer totalReach) {
}
