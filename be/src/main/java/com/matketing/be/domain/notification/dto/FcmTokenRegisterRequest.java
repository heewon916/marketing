package com.matketing.be.domain.notification.dto;

import com.matketing.be.domain.notification.enums.DevicePlatform;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class FcmTokenRegisterRequest {
    @NotBlank(message = "Token is required")
    private String token;

    @NotNull(message = "Platform is required")
    private DevicePlatform platform;
}
