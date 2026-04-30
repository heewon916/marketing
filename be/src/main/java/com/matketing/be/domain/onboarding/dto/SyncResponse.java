package com.matketing.be.domain.onboarding.dto;

public record SyncResponse(
        boolean success,
        String message,
        String storeId
) {
}
