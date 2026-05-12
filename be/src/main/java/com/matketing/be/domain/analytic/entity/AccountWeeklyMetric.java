package com.matketing.be.domain.analytic.entity;

import com.matketing.be.domain.store.entity.Store;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "account_weekly_metrics")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class AccountWeeklyMetric {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", nullable = false, updatable = false)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "store_id")
    private Store store;

    @Column(name = "total_reach")
    private Integer totalReach;

    @Column(name = "target_post_count")
    private Integer targetPostCount;

    @Column(name = "actual_post_count")
    private Integer actualPostCount;

    @Column(name = "achievement_rate", precision = 5, scale = 2)
    private BigDecimal achievementRate;

    @Column(name = "visit_intent_score", precision = 5, scale = 2)
    private BigDecimal visitIntentScore;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "is_deleted")
    private Boolean isDeleted;

    @Column(name = "week_start")
    private LocalDate weekStart;

    @Column(name = "total_saves")
    private Integer totalSaves;

    @Column(name = "total_shares")
    private Integer totalShares;
}
