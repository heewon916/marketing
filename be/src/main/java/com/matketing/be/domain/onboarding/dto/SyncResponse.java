package com.matketing.be.domain.onboarding.dto;

import java.util.List;

public record SyncResponse(
        boolean success,
        String message,
        String storeId,
        String storeName,
        String suggestedCategory,
        List<Object> menus
) {
}
