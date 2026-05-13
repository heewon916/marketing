package com.matketing.be.domain.analytic.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.LocalDate;

public record VisitIntentResponse(
        @JsonProperty("week_start") LocalDate weekStart,
        @JsonProperty("week_end") LocalDate weekEnd,
        @JsonProperty("visit_intent_score") BigDecimal visitIntentScore,
        Breakdown breakdown) {
    public record Breakdown(
            Integer reach,
            Integer saves,
            Integer shares) {
    }
}
