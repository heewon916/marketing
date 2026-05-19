package com.matketing.be.domain.user.service;

import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.domain.user.dto.SimpleApiResponse;
import com.matketing.be.domain.user.dto.StoreUpdatePatchRequest;
import com.matketing.be.domain.user.dto.SyncInstagramResponse;
import com.matketing.be.domain.user.dto.UserMeResponse;
import com.matketing.be.domain.user.entity.User;
import com.matketing.be.domain.user.repository.UserRepository;
import com.matketing.be.domain.store.repository.MenuRepository;
import com.matketing.be.domain.store.repository.StoreHoursRepository;
import com.matketing.be.domain.analytic.repository.AccountWeeklyMetricRepository;
import com.matketing.be.domain.analytic.repository.InstagramMetricRepository;
import com.matketing.be.domain.content.repository.ContentRepository;
import com.matketing.be.domain.notification.repository.DeviceTokenRepository;
import com.matketing.be.domain.notification.repository.NotificationRepository;
import com.matketing.be.domain.content.entity.Content;
import com.matketing.be.global.auth.oauth2.InstagramApiClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final StoreRepository storeRepository;
    private final ObjectMapper objectMapper;
    private final InstagramApiClient instagramApiClient;
    
    private final MenuRepository menuRepository;
    private final StoreHoursRepository storeHoursRepository;
    private final AccountWeeklyMetricRepository accountWeeklyMetricRepository;
    private final InstagramMetricRepository instagramMetricRepository;
    private final ContentRepository contentRepository;
    private final DeviceTokenRepository deviceTokenRepository;
    private final NotificationRepository notificationRepository;

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
                store.getStoreName(),
                store.getCategory() != null ? store.getCategory().name() : null,
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
            store.updateSyncInfo(null, null, request.category());
        }
        if (request.address() != null) {
            store.updateDetails(null, request.address(), null, null, null);
        }
        if (request.operatingHours() != null) {
            try {
                String hoursJson = objectMapper.writeValueAsString(request.operatingHours());
                store.updateDetails(null, null, null, null, hoursJson);
            } catch (JsonProcessingException e) {
                throw new IllegalArgumentException("영업시간 형식이 올바르지 않습니다.");
            }
        }

        return new SimpleApiResponse(true, "매장 정보가 성공적으로 수정되었습니다.");
    }

    @Transactional
    public SimpleApiResponse deleteUser(User user) {
        log.info("[DeleteUser] 탈퇴 프로세스 시작 - userId: {}", user.getId());

        try {
            deviceTokenRepository.deleteAllByUserId(user.getId());
            log.info("[DeleteUser] DeviceToken 삭제 성공 - userId: {}", user.getId());
        } catch (Exception e) {
            log.error("[DeleteUser] DeviceToken 삭제 실패 - userId: {}", user.getId(), e);
            throw e;
        }

        storeRepository.findFirstByUserId(user.getId()).ifPresent(store -> {
            UUID storeId = store.getId();
            log.info("[DeleteUser] 매장 확인 완료 - storeId: {}, userId: {}", storeId, user.getId());
            
            try {
                menuRepository.deleteAllByStoreId(storeId);
                log.info("[DeleteUser] Menu 삭제 성공 - storeId: {}", storeId);
            } catch (Exception e) {
                log.error("[DeleteUser] Menu 삭제 실패 - storeId: {}", storeId, e);
                throw e;
            }

            try {
                storeHoursRepository.deleteAllByStoreId(storeId);
                log.info("[DeleteUser] StoreHours 삭제 성공 - storeId: {}", storeId);
            } catch (Exception e) {
                log.error("[DeleteUser] StoreHours 삭제 실패 - storeId: {}", storeId, e);
                throw e;
            }

            try {
                accountWeeklyMetricRepository.deleteAllByStore_Id(storeId);
                log.info("[DeleteUser] AccountWeeklyMetric 삭제 성공 - storeId: {}", storeId);
            } catch (Exception e) {
                log.error("[DeleteUser] AccountWeeklyMetric 삭제 실패 - storeId: {}", storeId, e);
                throw e;
            }

            try {
                instagramMetricRepository.deleteAllByStore_Id(storeId);
                log.info("[DeleteUser] InstagramMetric 삭제 성공 - storeId: {}", storeId);
            } catch (Exception e) {
                log.error("[DeleteUser] InstagramMetric 삭제 실패 - storeId: {}", storeId, e);
                throw e;
            }

            try {
                List<Content> contents = contentRepository.findByStoreId(storeId);
                log.info("[DeleteUser] 삭제 대상 Content 조회 완료 - {} 건", contents.size());
                contentRepository.deleteAll(contents);
                log.info("[DeleteUser] Content 삭제 성공 - storeId: {}", storeId);
            } catch (Exception e) {
                log.error("[DeleteUser] Content 삭제 실패 - storeId: {}", storeId, e);
                throw e;
            }

            try {
                notificationRepository.deleteAllByStoreId(storeId);
                log.info("[DeleteUser] Notification 삭제 성공 - storeId: {}", storeId);
            } catch (Exception e) {
                log.error("[DeleteUser] Notification 삭제 실패 - storeId: {}", storeId, e);
                throw e;
            }
            
            try {
                storeRepository.delete(store);
                log.info("[DeleteUser] Store 삭제 성공 - storeId: {}", storeId);
            } catch (Exception e) {
                log.error("[DeleteUser] Store 삭제 실패 - storeId: {}", storeId, e);
                throw e;
            }
        });

        try {
            userRepository.delete(user);
            log.info("[DeleteUser] User 삭제 성공 - userId: {}", user.getId());
        } catch (Exception e) {
            log.error("[DeleteUser] User 삭제 실패 - userId: {}", user.getId(), e);
            throw e;
        }

        return new SimpleApiResponse(true, "회원 탈퇴가 완료되었습니다.");
    }

    @Transactional
    public SyncInstagramResponse syncInstagram(User user) {
        String accessToken = user.getAccessToken();
        if (accessToken == null || accessToken.isEmpty()) {
            throw new IllegalArgumentException("인스타그램 연동 토큰이 존재하지 않습니다.");
        }

        Map<String, Object> profile = instagramApiClient.getUserProfile(accessToken);
        if (profile == null) {
            throw new IllegalArgumentException("인스타그램 프로필 정보를 가져오는데 실패했습니다.");
        }

        String updatedUsername = profile.get("username") != null ? profile.get("username").toString() : user.getInstagramUsername();
        String updatedProfileImageUrl = profile.get("profile_picture_url") != null ? profile.get("profile_picture_url").toString() : user.getProfileImageUrl();

        // 만약 여전히 프로필 이미지 URL이 없다면 기본값 사용 (선택 사항)
        if (updatedProfileImageUrl == null) {
            updatedProfileImageUrl = "https://mock-image-url.com/profile.jpg";
        }

        user.updateProfile(updatedUsername, updatedProfileImageUrl);

        SyncInstagramResponse.InstagramData data = new SyncInstagramResponse.InstagramData(
                user.getInstagramUserId(),
                updatedUsername,
                updatedProfileImageUrl
        );

        return new SyncInstagramResponse(true, "인스타그램 프로필 정보가 성공적으로 동기화되었습니다.", data);
    }
}
