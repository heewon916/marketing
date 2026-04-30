package com.matketing.be.domain.notification.controller;

import com.matketing.be.domain.notification.dto.TestNotificationSendRequest;
import com.matketing.be.domain.notification.dto.TestNotificationSendResponse;
import com.matketing.be.domain.notification.entity.DeviceToken;
import com.matketing.be.domain.notification.repository.DeviceTokenRepository;
import com.matketing.be.domain.notification.service.FcmPushService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.OffsetDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/v1/internal/notifications")
@RequiredArgsConstructor
public class InternalNotificationTestController {

    private final DeviceTokenRepository deviceTokenRepository;
    private final FcmPushService fcmPushService;

    // TODO: 추후 관리자/내부 서비스 인증을 거치도록 Security 설정 필요
    @PostMapping("/test-send")
    public ResponseEntity<TestNotificationSendResponse> sendTestNotification(
            @Valid @RequestBody TestNotificationSendRequest request) {
        
        List<DeviceToken> activeTokens = deviceTokenRepository.findByUserIdAndIsActiveTrue(request.getUserId());

        int[] result = fcmPushService.sendPushNotification(
                activeTokens,
                request.getTitle(),
                request.getBody(),
                request.getWebUrl()
        );

        TestNotificationSendResponse response = TestNotificationSendResponse.builder()
                .status("success")
                .sentCount(result[0])
                .failedCount(result[1])
                .sentAt(OffsetDateTime.now())
                .build();

        return ResponseEntity.ok(response);
    }
}
