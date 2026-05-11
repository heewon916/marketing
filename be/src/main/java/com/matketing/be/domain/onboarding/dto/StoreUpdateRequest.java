package com.matketing.be.domain.onboarding.dto;

import com.matketing.be.domain.store.entity.CategoryEnumType;
import com.matketing.be.domain.store.entity.OwnerPersonaEnumType;
import java.math.BigDecimal;

public record StoreUpdateRequest(
        String storeName,
        CategoryEnumType category,
        OwnerPersonaEnumType ownerPersona,
        String address,
        BigDecimal latitude,
        BigDecimal longitude,
        String operatingHours
) {
}
