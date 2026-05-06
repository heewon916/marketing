package com.matketing.be.domain.notification.controller;

import com.matketing.be.domain.notification.dto.FcmTokenRegisterRequest;
import com.matketing.be.domain.notification.dto.FcmTokenRegisterResponse;
import com.matketing.be.domain.notification.service.DeviceTokenService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users/me/fcm-token")
@RequiredArgsConstructor
public class FcmTokenController {

    private final DeviceTokenService deviceTokenService;

    // 현재 로그인한 사용자의 FCM 기기 토큰을 등록하거나 갱신한다.
    @PostMapping
    public ResponseEntity<FcmTokenRegisterResponse> registerToken(@Valid @RequestBody FcmTokenRegisterRequest request) {
        // TODO: Spring Security 적용 후 SecurityContextHolder에서 추출하도록 수정 필요
        // 임시로 고정된 UUID 사용 (또는 헤더/세션에서 받아오도록 처리)
        UUID currentUserId = UUID.fromString("00000000-0000-0000-0000-000000000000"); // 임시 유저 ID

        FcmTokenRegisterResponse response = deviceTokenService.registerOrUpdateToken(currentUserId, request);
        return ResponseEntity.ok(response);
    }
}
