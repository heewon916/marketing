package com.matketing.be.domain.onboarding.dto;

import java.math.BigDecimal;

public record StoreUpdateRequest(
        String storeName,
        String category,
        String ownerPersona,
        String address,
        BigDecimal latitude,
        BigDecimal longitude,
        String operatingHours
) {
}
