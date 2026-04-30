package com.matketing.be.domain.notification.dto;

import com.matketing.be.domain.notification.entity.DeviceToken;
import com.matketing.be.domain.notification.enums.DevicePlatform;
import lombok.Builder;
import lombok.Getter;

import java.time.OffsetDateTime;
import java.util.UUID;

@Getter
@Builder
public class FcmTokenRegisterResponse {
    private UUID deviceTokenId;
    private DevicePlatform platform;
    private boolean isActive;
    private OffsetDateTime updatedAt;

    public static FcmTokenRegisterResponse from(DeviceToken deviceToken) {
        return FcmTokenRegisterResponse.builder()
                .deviceTokenId(deviceToken.getId())
                .platform(deviceToken.getPlatform())
                .isActive(deviceToken.isActive())
                .updatedAt(deviceToken.getUpdatedAt())
                .build();
    }
}
