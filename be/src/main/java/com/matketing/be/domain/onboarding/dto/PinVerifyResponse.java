package com.matketing.be.domain.onboarding.dto;

public record PinVerifyResponse(
        boolean success,
        String merchantId,
        String message
) {
}
