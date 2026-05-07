package com.matketing.be.domain.notification.controller;

import com.matketing.be.domain.notification.dto.FcmTokenRegisterRequest;
import com.matketing.be.domain.notification.dto.FcmTokenRegisterResponse;
import com.matketing.be.domain.notification.service.DeviceTokenService;
import com.matketing.be.domain.user.entity.User;
import com.matketing.be.domain.user.repository.UserRepository;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users/me/fcm-token")
@RequiredArgsConstructor
public class FcmTokenController {

    private final DeviceTokenService deviceTokenService;
    private final UserRepository userRepository;

    // 현재 로그인한 사용자의 FCM 기기 토큰을 등록하거나 갱신한다.
    @PostMapping
    public ResponseEntity<FcmTokenRegisterResponse> registerToken(@Valid @RequestBody FcmTokenRegisterRequest request) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated() || "anonymousUser".equals(authentication.getPrincipal())) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED_USER);
        }

        String instagramUserId = authentication.getName();
        User user = userRepository.findByInstagramUserId(instagramUserId)
                .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));

        UUID currentUserId = user.getId();

        FcmTokenRegisterResponse response = deviceTokenService.registerOrUpdateToken(currentUserId, request);
        return ResponseEntity.ok(response);
    }
}
