package com.matketing.be.domain.notification.controller;

import com.matketing.be.domain.notification.dto.FcmTokenRegisterRequest;
import com.matketing.be.domain.notification.dto.FcmTokenRegisterResponse;
import com.matketing.be.domain.notification.service.DeviceTokenService;
import com.matketing.be.global.auth.jwt.AuthUser;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users/me/fcm-token")
@RequiredArgsConstructor
public class FcmTokenController {

    private final DeviceTokenService deviceTokenService;

    // 현재 로그인한 사용자의 FCM 기기 토큰을 등록하거나 갱신한다.
    @PostMapping
    public ResponseEntity<FcmTokenRegisterResponse> registerToken(
            @Valid @RequestBody FcmTokenRegisterRequest request,
            @AuthenticationPrincipal AuthUser authUser) {
        
        if (authUser == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED_USER);
        }

        UUID currentUserId = authUser.getId();

        FcmTokenRegisterResponse response = deviceTokenService.registerOrUpdateToken(currentUserId, request);
        return ResponseEntity.ok(response);
    }
}
