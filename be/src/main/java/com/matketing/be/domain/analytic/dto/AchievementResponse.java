package com.matketing.be.domain.analytic.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.LocalDate;

public record AchievementResponse(
        @JsonProperty("week_start") LocalDate weekStart,
        @JsonProperty("week_end") LocalDate weekEnd,
        @JsonProperty("target_post_count") Integer targetPostCount,
        @JsonProperty("actual_post_count") Integer actualPostCount,
        @JsonProperty("achievement_rate") BigDecimal achievementRate) {
}
