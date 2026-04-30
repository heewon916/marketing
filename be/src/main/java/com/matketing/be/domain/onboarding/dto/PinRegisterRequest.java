package com.matketing.be.domain.onboarding.dto;

public record PinRegisterRequest(
        String pin,
        String merchantId
) {
}
