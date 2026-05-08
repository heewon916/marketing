package com.matketing.be.domain.user.dto;

import com.matketing.be.domain.store.entity.CategoryEnumType;
import java.util.Map;

public record StoreUpdatePatchRequest(
    CategoryEnumType category,
    String address,
    Map<String, Object> operatingHours
) {}
