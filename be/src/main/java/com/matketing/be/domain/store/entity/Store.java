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

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "stores")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Store {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId; // User 엔티티와 연관관계 매핑 필요 시 변경

    @Column(name = "merchant_id", length = 20)
    private String merchantId;

    @Column(name = "store_name", nullable = false, length = 200)
    private String storeName;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "category", columnDefinition = "category_type")
    private CategoryEnumType category;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "owner_persona", columnDefinition = "owner_persona_type")
    private OwnerPersonaEnumType ownerPersona;

    @Column(name = "address", columnDefinition = "TEXT")
    private String address;

    @Column(name = "latitude", precision = 10, scale = 7)
    private BigDecimal latitude;

    @Column(name = "longitude", precision = 10, scale = 7)
    private BigDecimal longitude;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "operating_hours", columnDefinition = "jsonb")
    private String operatingHours;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;

    @Builder
    public Store(UUID userId, String merchantId, String storeName, CategoryEnumType category, OwnerPersonaEnumType ownerPersona, String address, BigDecimal latitude, BigDecimal longitude, String operatingHours) {
        this.userId = userId;
        this.merchantId = merchantId;
        this.storeName = storeName;
        this.category = category;
        this.ownerPersona = ownerPersona;
        this.address = address;
        this.latitude = latitude;
        this.longitude = longitude;
        this.operatingHours = operatingHours;
    }

    public void updateAllDetails(String merchantId, String storeName, CategoryEnumType category, OwnerPersonaEnumType ownerPersona, String address, BigDecimal latitude, BigDecimal longitude, String operatingHours) {
        if (merchantId != null) this.merchantId = merchantId;
        if (storeName != null) this.storeName = storeName;
        if (category != null) this.category = category;
        if (ownerPersona != null) this.ownerPersona = ownerPersona;
        if (address != null) this.address = address;
        if (latitude != null) this.latitude = latitude;
        if (longitude != null) this.longitude = longitude;
        if (operatingHours != null) this.operatingHours = operatingHours;
    }
}
