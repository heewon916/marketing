package com.matketing.be.domain.user.service;

import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.domain.user.dto.SimpleApiResponse;
import com.matketing.be.domain.user.dto.StoreUpdatePatchRequest;
import com.matketing.be.domain.user.dto.SyncInstagramResponse;
import com.matketing.be.domain.user.dto.UserMeResponse;
import com.matketing.be.domain.user.entity.User;
import com.matketing.be.domain.user.repository.UserRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final StoreRepository storeRepository;
    private final ObjectMapper objectMapper;

    @Transactional(readOnly = true)
    public UserMeResponse getMe(User user) {
        Optional<Store> storeOpt = storeRepository.findFirstByUserId(user.getId());
        
        UserMeResponse.UserDto userDto = new UserMeResponse.UserDto(
                user.getId().toString(),
                user.getInstagramUserId(),
                user.getInstagramUsername(),
                user.getProfileImageUrl()
        );

        if (storeOpt.isEmpty()) {
            return new UserMeResponse(userDto, null, false);
        }

        Store store = storeOpt.get();
        Object operatingHoursObj = null;
        if (store.getOperatingHours() != null && !store.getOperatingHours().isEmpty()) {
            try {
                operatingHoursObj = objectMapper.readValue(store.getOperatingHours(), Map.class);
            } catch (JsonProcessingException e) {
                log.warn("Failed to parse operatingHours JSON", e);
            }
        }

        boolean isOnboarded = store.getLatitude() != null && store.getLongitude() != null && operatingHoursObj != null;

        UserMeResponse.StoreDto storeDto = new UserMeResponse.StoreDto(
                store.getId().toString(),
                store.getMerchantId(),
                store.getCategory(),
                store.getAddress(),
                operatingHoursObj
        );

        return new UserMeResponse(userDto, storeDto, isOnboarded);
    }

    @Transactional
    public SimpleApiResponse updateStore(User user, StoreUpdatePatchRequest request) {
        Store store = storeRepository.findFirstByUserId(user.getId())
                .orElseThrow(() -> new IllegalArgumentException("매장 정보가 없습니다."));

        if (request.category() != null) {
            store.updateAllDetails(null, request.category(), null, null, null, null, null);
        }
        if (request.address() != null) {
            store.updateAllDetails(null, null, null, request.address(), null, null, null);
        }
        if (request.operatingHours() != null) {
            try {
                String hoursJson = objectMapper.writeValueAsString(request.operatingHours());
                store.updateAllDetails(null, null, null, null, null, null, hoursJson);
            } catch (JsonProcessingException e) {
                throw new IllegalArgumentException("영업시간 형식이 올바르지 않습니다.");
            }
        }

        return new SimpleApiResponse(true, "매장 정보가 성공적으로 수정되었습니다.");
    }

    @Transactional
    public SimpleApiResponse deleteUser(User user) {
        // 실제 프로덕션에서는 관련된 매장, 메뉴, 운영시간 등을 CASCADE 처리하거나 Soft Delete 처리
        // 여기서는 MVP 수준으로 Hard Delete를 가정 (또는 Repository에 맞게 처리)
        // Store 삭제
        storeRepository.findFirstByUserId(user.getId()).ifPresent(storeRepository::delete);
        // User 삭제
        userRepository.delete(user);

        return new SimpleApiResponse(true, "회원 탈퇴가 완료되었습니다.");
    }

    @Transactional
    public SyncInstagramResponse syncInstagram(User user) {
        // Graph API 연동 로직이 필요하지만 MVP에서는 Mock 업데이트 처리
        
        // MVP Mock
        String updatedUsername = user.getInstagramUsername();
        String updatedProfileImageUrl = user.getProfileImageUrl() != null ? user.getProfileImageUrl() : "https://mock-image-url.com/profile.jpg";

        user.updateProfile(updatedUsername, updatedProfileImageUrl);

        SyncInstagramResponse.InstagramData data = new SyncInstagramResponse.InstagramData(
                user.getInstagramUserId(),
                updatedUsername,
                updatedProfileImageUrl
        );

        return new SyncInstagramResponse(true, "인스타그램 프로필 정보가 성공적으로 동기화되었습니다.", data);
    }
}
