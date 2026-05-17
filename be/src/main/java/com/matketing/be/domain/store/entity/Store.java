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

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private com.matketing.be.domain.user.entity.User user;

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

    @OneToMany(mappedBy = "store", cascade = CascadeType.ALL, orphanRemoval = true)
    private java.util.List<Menu> menus = new java.util.ArrayList<>();

    // User 엔티티의 ID를 반환하는 편의 메서드 (기존 코드 호환성 유지)
    public UUID getUserId() {
        return this.user != null ? this.user.getId() : null;
    }

    @Builder
    public Store(com.matketing.be.domain.user.entity.User user, String merchantId, String storeName, CategoryEnumType category, OwnerPersonaEnumType ownerPersona, String address, BigDecimal latitude, BigDecimal longitude, String operatingHours) {
        this.user = user;
        this.merchantId = merchantId;
        this.storeName = storeName;
        this.category = category;
        this.ownerPersona = ownerPersona;
        this.address = address;
        this.latitude = latitude;
        this.longitude = longitude;
        this.operatingHours = operatingHours;
    }

    public void updateSyncInfo(String merchantId, String storeName, CategoryEnumType category) {
        if (merchantId != null) this.merchantId = merchantId;
        if (storeName != null) this.storeName = storeName;
        if (category != null) this.category = category;
    }

    public void updateDetails(OwnerPersonaEnumType ownerPersona, String address, BigDecimal latitude, BigDecimal longitude, String operatingHours) {
        if (ownerPersona != null) this.ownerPersona = ownerPersona;
        if (address != null) this.address = address;
        if (latitude != null) this.latitude = latitude;
        if (longitude != null) this.longitude = longitude;
        if (operatingHours != null) this.operatingHours = operatingHours;
    }
}
