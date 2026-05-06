package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.dto.FcmTokenRegisterRequest;
import com.matketing.be.domain.notification.dto.FcmTokenRegisterResponse;
import com.matketing.be.domain.notification.entity.DeviceToken;
import com.matketing.be.domain.notification.repository.DeviceTokenRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class DeviceTokenService {

    private final DeviceTokenRepository deviceTokenRepository;

    // 현재 사용자의 FCM 기기 토큰을 등록하거나 기존 토큰을 갱신한다.
    @Transactional
    public FcmTokenRegisterResponse registerOrUpdateToken(UUID userId, FcmTokenRegisterRequest request) {
        // 기존 같은 유저의 active 토큰들 모두 비활성화 처리
        List<DeviceToken> activeTokens = deviceTokenRepository.findByUserIdAndIsActiveTrue(userId);
        for (DeviceToken t : activeTokens) {
            if (!t.getToken().equals(request.getToken())) {
                t.deactivate();
            }
        }

        // 해당 토큰 값이 이미 존재하는지 확인
        Optional<DeviceToken> existingTokenOpt = deviceTokenRepository.findByToken(request.getToken());

        DeviceToken deviceToken;
        if (existingTokenOpt.isPresent()) {
            deviceToken = existingTokenOpt.get();
            deviceToken.updateToken(request.getToken(), request.getPlatform());
        } else {
            deviceToken = DeviceToken.builder()
                    .userId(userId)
                    .token(request.getToken())
                    .platform(request.getPlatform())
                    .isActive(true)
                    .build();
        }

        deviceTokenRepository.save(deviceToken);

        return FcmTokenRegisterResponse.from(deviceToken);
    }
}
