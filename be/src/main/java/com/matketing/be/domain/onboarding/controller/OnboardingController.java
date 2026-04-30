package com.matketing.be.domain.onboarding.controller;

import com.matketing.be.domain.onboarding.dto.PinRegisterRequest;
import com.matketing.be.domain.onboarding.dto.PinVerifyRequest;
import com.matketing.be.domain.onboarding.dto.PinVerifyResponse;
import com.matketing.be.domain.onboarding.service.OnboardingService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/onboarding/pin")
@RequiredArgsConstructor
public class OnboardingController {

    private final OnboardingService onboardingService;

    // [API 1] POS 플러그인에서 난수와 가맹점 식별자를 등록
    @PostMapping("/register")
    public ResponseEntity<Map<String, String>> registerPin(@RequestBody PinRegisterRequest request) {
        if (request.pin() == null || request.merchantId() == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "Missing required fields"));
        }

        onboardingService.registerPin(request.pin(), request.merchantId());
        return ResponseEntity.ok(Map.of("message", "등록 성공"));
    }

    // [API 2] 외부(모바일/웹)에서 난수를 입력해 가맹점 정보를 가져감
    @PostMapping("/verify")
    public ResponseEntity<PinVerifyResponse> verifyPin(@RequestBody PinVerifyRequest request) {
        if (request.pin() == null) {
            return ResponseEntity.badRequest().body(new PinVerifyResponse(false, null, "PIN is required"));
        }

        PinVerifyResponse response = onboardingService.verifyPin(request.pin());

        if (response.success()) {
            return ResponseEntity.ok(response);
        } else {
            return ResponseEntity.status(404).body(response);
        }
    }
}
