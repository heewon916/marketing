package com.matketing.be.domain.onboarding.service;

import com.matketing.be.domain.onboarding.dto.PinVerifyResponse;
import com.matketing.be.domain.onboarding.dto.SyncResponse;
import com.matketing.be.domain.onboarding.entity.PosPin;
import com.matketing.be.domain.onboarding.repository.PosPinRepository;
import com.matketing.be.domain.store.entity.CategoryEnumType;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.entity.Menu;
import com.matketing.be.domain.store.entity.StoreHours;
import com.matketing.be.domain.store.repository.MenuRepository;
import com.matketing.be.domain.store.repository.StoreHoursRepository;
import com.matketing.be.domain.store.repository.StoreRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class OnboardingService {

    private static final String KEY_STATUS = "status";
    private static final String KEY_SUCCESS = "success";
    private static final String KEY_DATA = "data";
    private static final String KEY_PLACE_ID = "place_id";
    private static final String KEY_ADDRESS = "address";
    private static final String KEY_BUSINESS_HOURS = "business_hours";
    private static final String KEY_MENUS = "menus";
    private static final String KEY_MENU_NAME = "menu_name";
    private static final String KEY_PRICE = "price";
    private static final String KEY_MENU_DESCRIPTION = "menu_description";
    private static final String KEY_RESULT_TYPE = "resultType";
    private static final String KEY_NAME = "name";

    private final PosPinRepository posPinRepository;
    private final StoreRepository storeRepository;
    private final MenuRepository menuRepository;
    private final StoreHoursRepository storeHoursRepository;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${TOSS_ACCESS_KEY:}")
    private String tossAccessKey;

    @Value("${TOSS_SECRET_KEY:}")
    private String tossSecretKey;

    @Value("${FASTAPI_BASE_URL:http://fastapi:8000}")
    private String fastapiBaseUrl;

    public void registerPin(String pin, String merchantId) {
        log.info("Registering PIN: {} for merchant: {}", pin, merchantId);
        try {
            java.nio.file.Files.writeString(java.nio.file.Paths.get("/app/pin_debug.log"), "REGISTER: " + pin + " for " + merchantId + "\n", java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND);
        } catch(Exception e) {}

        // Redis에 난수와 merchantId 저장 (엔티티에 설정된 TTL 3분 자동 적용)
        posPinRepository.save(PosPin.builder()
                .pin(pin)
                .merchantId(merchantId)
                .build());
    }

    public PinVerifyResponse verifyPin(String pin) {
        log.info("Verifying PIN: {}", pin);
        try {
            java.nio.file.Files.writeString(java.nio.file.Paths.get("/app/pin_debug.log"), "VERIFY: " + pin + "\n", java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND);
        } catch(Exception e) {}

        Optional<PosPin> posPinOptional = posPinRepository.findById(pin);

        if (posPinOptional.isPresent()) {
            PosPin posPin = posPinOptional.get();
            String merchantId = posPin.getMerchantId();

            // 보안을 위해 1회 조회 후 즉시 삭제 (One-Time 사용)
            posPinRepository.deleteById(pin);

            return new PinVerifyResponse(true, merchantId, "검증 성공");
        } else {
            return new PinVerifyResponse(false, null, "유효하지 않거나 만료된 PIN 번호입니다.");
        }
    }

    @Transactional
    public void invalidatePin(String pin) {
        posPinRepository.deleteById(pin);
    }

    @Transactional
    public SyncResponse syncStoreData(UUID userId, String merchantId) {
        log.info("Starting sync for user: {}, merchant: {}", userId, merchantId);

        String storeName = getMerchantNameFromToss(merchantId);
        CategoryEnumType category = CategoryEnumType.카페; // Toss API에서 category를 주지 않으므로 기본값 또는 추후 연동

        Map<String, String> placeInfo = fetchPlaceInfo(storeName);
        String placeId = placeInfo.get(KEY_PLACE_ID);
        String address = placeInfo.getOrDefault(KEY_ADDRESS, "");

        Store store = storeRepository.save(Store.builder()
                .userId(userId)
                .merchantId(merchantId)
                .storeName(storeName)
                .category(category)
                .address(address)
                .build());

        if (placeId != null && !placeId.isEmpty()) {
            fetchAndSaveStoreDetails(placeId, store);
        }

        log.info("Successfully synced store data for merchantId: {}", merchantId);
        return new SyncResponse(true, "가맹점 정보 동기화 및 DB 저장 완료", store.getId().toString(), storeName, null, null);
    }

    @Transactional
    public SyncResponse updateStoreData(UUID storeId, UUID userId, com.matketing.be.domain.onboarding.dto.StoreUpdateRequest request) {
        Store store = storeRepository.findById(storeId)
                .orElseThrow(() -> new IllegalArgumentException("Store not found"));

        if (!store.getUserId().equals(userId)) {
            throw new IllegalArgumentException("Not authorized to update this store");
        }

        store.updateAllDetails(
                request.storeName(),
                request.category(),
                request.ownerPersona(),
                request.address(),
                request.latitude(),
                request.longitude(),
                request.operatingHours()
        );

        return new SyncResponse(true, "Store data updated successfully", store.getId().toString(), store.getStoreName(), null, null);
    }

    private Map<String, String> fetchPlaceInfo(String storeName) {
        try {
            Map<String, Object> searchResult = searchPlacesViaCrawler(storeName);
            if (searchResult == null || !KEY_SUCCESS.equals(searchResult.get(KEY_STATUS))) {
                return Map.of();
            }

            Object dataObj = searchResult.get(KEY_DATA);
            if (!(dataObj instanceof List<?> dataList) || dataList.isEmpty()) {
                return Map.of();
            }

            Object firstPlaceObj = dataList.getFirst();
            if (!(firstPlaceObj instanceof Map<?, ?> firstPlace)) {
                return Map.of();
            }

            String pId = firstPlace.get(KEY_PLACE_ID) instanceof String s ? s : null;
            String addr = firstPlace.get(KEY_ADDRESS) instanceof String s ? s : "";
            return Map.of(KEY_PLACE_ID, pId == null ? "" : pId, KEY_ADDRESS, addr);
        } catch (Exception e) {
            log.warn("Crawler search failed for keyword {}: {}", storeName, e.getMessage());
        }
        return Map.of();
    }

    private void fetchAndSaveStoreDetails(String placeId, Store store) {
        try {
            Map<String, Object> detailResult = getPlaceDetailViaCrawler(placeId);
            if (detailResult == null || !KEY_SUCCESS.equals(detailResult.get(KEY_STATUS))) return;

            Object dataObj = detailResult.get(KEY_DATA);
            if (!(dataObj instanceof Map<?, ?> dataMap)) return;

            saveStoreHours(store, dataMap.get(KEY_BUSINESS_HOURS));
            saveMenus(store, dataMap.get(KEY_MENUS));

        } catch (Exception e) {
            log.warn("Crawler detail failed for placeId {}: {}", placeId, e.getMessage());
        }
    }

    private void saveStoreHours(Store store, Object hoursObj) {
        if (!(hoursObj instanceof Map<?, ?> hoursMap)) return;

        StoreHours storeHours = StoreHours.builder()
                .store(store)
                .mondayOpen(parseTime(hoursMap.get("mon_hours"), true))
                .mondayClose(parseTime(hoursMap.get("mon_hours"), false))
                .tuesdayOpen(parseTime(hoursMap.get("tues_hours"), true))
                .tuesdayClose(parseTime(hoursMap.get("tues_hours"), false))
                .wednesdayOpen(parseTime(hoursMap.get("wed_hours"), true))
                .wednesdayClose(parseTime(hoursMap.get("wed_hours"), false))
                .thursdayOpen(parseTime(hoursMap.get("thur_hours"), true))
                .thursdayClose(parseTime(hoursMap.get("thur_hours"), false))
                .fridayOpen(parseTime(hoursMap.get("fri_hours"), true))
                .fridayClose(parseTime(hoursMap.get("fri_hours"), false))
                .saturdayOpen(parseTime(hoursMap.get("sat_hours"), true))
                .saturdayClose(parseTime(hoursMap.get("sat_hours"), false))
                .sundayOpen(parseTime(hoursMap.get("sun_hours"), true))
                .sundayClose(parseTime(hoursMap.get("sun_hours"), false))
                .build();
        storeHoursRepository.save(storeHours);
    }

    private void saveMenus(Store store, Object menusObj) {
        if (!(menusObj instanceof List<?> menusList)) return;

        for (Object menuObj : menusList) {
            if (!(menuObj instanceof Map<?, ?> menuMap)) continue;

            String menuName = menuMap.get(KEY_MENU_NAME) instanceof String s ? s : "이름 없음";
            Integer price = menuMap.get(KEY_PRICE) instanceof Number n ? n.intValue() : 0;
            String description = menuMap.get(KEY_MENU_DESCRIPTION) instanceof String s ? s : null;

            Menu menu = Menu.builder()
                    .store(store)
                    .name(menuName)
                    .price(price)
                    .description(description)
                    .build();
            menuRepository.save(menu);
        }
    }

    private LocalTime parseTime(Object timeRangeObj, boolean isOpen) {
        if (!(timeRangeObj instanceof String timeRange) || timeRange.isEmpty() || "휴무".equals(timeRange)) {
            return null;
        }
        try {
            String[] parts = timeRange.split("-");
            if (parts.length == 2) {
                String timeStr = isOpen ? parts[0].trim() : parts[1].trim();
                if ("24:00".equals(timeStr)) return LocalTime.MAX;
                return LocalTime.parse(timeStr);
            }
        } catch (Exception e) {
            log.trace("Failed to parse time range: {}", timeRange);
        }
        return null;
    }

    private String getMerchantNameFromToss(String merchantId) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("x-access-key", tossAccessKey);
            headers.set("x-secret-key", tossSecretKey);
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(headers);
            String url = "https://open-api.tossplace.com/api-public/openapi/v1/merchants/" + merchantId;

            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url, HttpMethod.GET, entity, new ParameterizedTypeReference<>() {});

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> body = response.getBody();
                if ("SUCCESS".equals(body.get(KEY_RESULT_TYPE))) {
                    Object successObj = body.get(KEY_SUCCESS);
                    if (successObj instanceof Map<?, ?> successData && successData.containsKey(KEY_NAME)) {
                        Object nameObj = successData.get(KEY_NAME);
                        return nameObj instanceof String s ? s : "테스트 매장";
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Failed to fetch merchant info from Toss API for {}: {}", merchantId, e.getMessage());
        }
        return "테스트 매장";
    }

    public Map<String, Object> searchPlacesViaCrawler(String keyword) {
        String url = fastapiBaseUrl + "/api/search?keyword=" + keyword;
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                url, HttpMethod.GET, null, new ParameterizedTypeReference<>() {});
        return response.getBody();
    }

    public Map<String, Object> getPlaceDetailViaCrawler(String placeId) {
        String url = fastapiBaseUrl + "/api/place/" + placeId;
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                url, HttpMethod.GET, null, new ParameterizedTypeReference<>() {});
        return response.getBody();
    }
}
