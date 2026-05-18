package com.matketing.be.domain.store.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "menus")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Menu {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "store_id", nullable = false)
    private Store store;

    @Column(name = "name", nullable = false, length = 200)
    private String name;

    @Column(name = "price")
    private Integer price;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "weather_tags", columnDefinition = "jsonb")
    private String weatherTags;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "holiday_tags", columnDefinition = "jsonb")
    private String holidayTags;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;

    @Builder
    public Menu(Store store, String name, Integer price, String description, String weatherTags, String holidayTags) {
        this.store = store;
        this.name = name;
        this.price = price;
        this.description = description;
        this.weatherTags = weatherTags;
        this.holidayTags = holidayTags;
    }

    public void updateDescription(String description) {
        this.description = description;
    }
}
