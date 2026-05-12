package com.matketing.be.domain.analytic.entity;

import com.matketing.be.domain.content.entity.Content;
import com.matketing.be.domain.store.entity.Store;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "instagram_metrics")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class InstagramMetric {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", nullable = false, updatable = false)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "contents_id")
    private Content content;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "store_id")
    private Store store;

    @Column(name = "instagram_media_id", length = 100)
    private String instagramMediaId;

    @Column(name = "reaches")
    private Integer reaches;

    @Column(name = "saves")
    private Integer saves;

    @Column(name = "shares")
    private Integer shares;

    @Column(name = "likes")
    private Integer likes;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "week_start")
    private LocalDate weekStart;

    @Column(name = "week_end")
    private LocalDate weekEnd;
}
