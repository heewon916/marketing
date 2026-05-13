package com.matketing.be.domain.onboarding.controller;

import com.matketing.be.domain.onboarding.dto.PinRegisterRequest;
import com.matketing.be.domain.onboarding.dto.PinVerifyRequest;
import com.matketing.be.domain.onboarding.dto.PinVerifyResponse;
import com.matketing.be.domain.onboarding.dto.SyncRequest;
import com.matketing.be.domain.onboarding.dto.SyncResponse;
import com.matketing.be.domain.onboarding.service.OnboardingService;
import com.matketing.be.global.auth.jwt.AuthUser;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.matketing.be.domain.user.repository.UserRepository;
import com.matketing.be.domain.user.entity.User;
import com.matketing.be.domain.onboarding.dto.StoreUpdateRequest;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/onboarding")
@RequiredArgsConstructor
public class OnboardingController {

    private final OnboardingService onboardingService;
    private final UserRepository userRepository;

    // [API 1] POS 플러그인에서 난수와 가맹점 식별자
    @PostMapping("/pin/register")
    public ResponseEntity<Map<String, String>> registerPin(@RequestBody PinRegisterRequest request) {
        if (request.pin() == null || request.merchantId() == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "Missing required fields"));
        }

        onboardingService.registerPin(request.pin(), request.merchantId());
        return ResponseEntity.ok(Map.of("message", "등록 성공"));
    }

    // [API 2] 외부(모바일/웹)에서 난수를 입력해 가맹점 정보를 가져감
    @PostMapping("/pin/verify")
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

    // [API 3] Toss POS 연동 후 데이터 파이프라인(크롤링 및 DB 저장) 실행
    @PostMapping("/toss/sync")
    public ResponseEntity<SyncResponse> syncStoreData(
            @RequestBody SyncRequest request,
            @AuthenticationPrincipal AuthUser authUser) { // 인증된 사용자 정보 가져오기

        if (request.merchantId() == null) {
            return ResponseEntity.badRequest().body(new SyncResponse(false, "Merchant ID is required", null, null, null, null));
        }

        try {
            if (authUser == null) {
                throw new IllegalArgumentException("User not authenticated");
            }
            UUID userId = authUser.getId();
            SyncResponse response = onboardingService.syncStoreData(userId, request.merchantId());
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
             return ResponseEntity.status(401).body(new SyncResponse(false, "인증 오류: " + e.getMessage(), null, null, null, null));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(new SyncResponse(false, "동기화 실패: " + e.getMessage(), null, null, null, null));
        }
    }

    // [API 3-1] 온보딩 과정에서 유저가 수정한 가게 정보를 업데이트
    @PutMapping("/store/{storeId}")
    public ResponseEntity<SyncResponse> updateStoreData(
            @PathVariable UUID storeId,
            @RequestBody StoreUpdateRequest request,
            @AuthenticationPrincipal AuthUser authUser) {

        try {
            if (authUser == null) {
                throw new IllegalArgumentException("User not authenticated");
            }
            UUID userId = authUser.getId();
            SyncResponse response = onboardingService.updateStoreData(storeId, userId, request);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(new SyncResponse(false, "업데이트 실패: " + e.getMessage(), null, null, null, null));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(new SyncResponse(false, "업데이트 서버 오류: " + e.getMessage(), null, null, null, null));
        }
    }

    // [API 4] 프론트엔드 장소 검색 요청을 크롤러로 프록시 전달
    @org.springframework.web.bind.annotation.GetMapping("/search")
    public ResponseEntity<?> searchPlaces(
            @org.springframework.web.bind.annotation.RequestParam String keyword) {

        try {
            Object result = onboardingService.searchPlacesViaCrawler(keyword);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("success", false, "message", "크롤러 검색 실패: " + e.getMessage()));
        }
    }

    // [API 5] 프론트엔드 장소 상세 조회 요청을 크롤러로 프록시 전달
    @org.springframework.web.bind.annotation.GetMapping("/search/{placeId}")
    public ResponseEntity<?> getPlaceDetail(
            @org.springframework.web.bind.annotation.PathVariable String placeId) {

        try {
            Object result = onboardingService.getPlaceDetailViaCrawler(placeId);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("success", false, "message", "크롤러 상세 조회 실패: " + e.getMessage()));
        }
    }
}