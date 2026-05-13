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

    @Value("${CRAWLER_BASE_URL:http://crawler:8010}")
    private String crawlerBaseUrl;

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

        Store store = storeRepository.findFirstByUserId(userId).orElse(null);

        if (store != null) {
            // [기존 행 덮어쓰기 (Upsert - Update)]
            store.updateAllDetails(merchantId, storeName, CategoryEnumType.카페, null, "", null, null, null);

            // 중요: 이탈 전에 임시로 저장되었던 메뉴들이 중복으로 쌓이지 않게 싹 비워줍니다.
            menuRepository.deleteAllByStoreId(store.getId());
        } else {
            // [신규 생성 (Upsert - Insert)]
            store = Store.builder()
                    .userId(userId)
                    .merchantId(merchantId)
                    .storeName(storeName)
                    .category(CategoryEnumType.카페) // 임시 기본값 수정
                    .address("")
                    .build();
            store = storeRepository.save(store); // 신규일 때만 save
        }

        // 2. 토스에서 정확한 메뉴 리스트 가져오기 및 DB 즉시 저장
        List<Menu> tossMenus = fetchMenusFromToss(merchantId, store);
        if (!tossMenus.isEmpty()) {
            menuRepository.saveAll(tossMenus);
        }

        // 3. 메뉴 이름들을 분석하여 카테고리 자동 유추 후 Store 업데이트
        CategoryEnumType guessedCategory = com.matketing.be.domain.onboarding.util.CategoryInferenceUtil.guessCategory(tossMenus);
        store.updateAllDetails(null, storeName, guessedCategory, null, "", null, null, null);

        log.info("Successfully synced Toss store data for merchantId: {}", merchantId);

        // 프론트엔드로 전달할 메뉴 리스트 변환 (간소화)
        List<Object> responseMenus = tossMenus.stream()
            .map(m -> Map.of("name", m.getName(), "price", m.getPrice() != null ? m.getPrice() : 0))
            .collect(java.util.stream.Collectors.toList());

        return new SyncResponse(true, "가맹점 정보 동기화 및 DB 저장 완료", store.getId().toString(), storeName, guessedCategory.name(), responseMenus);
    }

    private List<Menu> fetchMenusFromToss(String merchantId, Store store) {
        List<Menu> menus = new java.util.ArrayList<>();
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("x-access-key", tossAccessKey);
            headers.set("x-secret-key", tossSecretKey);
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(headers);
            String url = "https://open-api.tossplace.com/api-public/openapi/v1/merchants/" + merchantId + "/catalog/items?page=1&size=100";

            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url, HttpMethod.GET, entity, new ParameterizedTypeReference<>() {});

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> body = response.getBody();
                if ("SUCCESS".equals(body.get(KEY_RESULT_TYPE))) {
                    Object successObj = body.get(KEY_SUCCESS);
                    if (successObj instanceof List<?> itemList) {
                        for (Object itemObj : itemList) {
                            if (itemObj instanceof Map<?, ?> itemMap) {
                                String title = itemMap.get("title") instanceof String s ? s : "이름 없음";
                                String description = itemMap.get("description") instanceof String s ? s : null;
                                int priceValue = 0;
                                Object priceObj = itemMap.get("price");
                                if (priceObj instanceof Map<?, ?> priceMap) {
                                    priceValue = priceMap.get("priceValue") instanceof Number n ? n.intValue() : 0;
                                }
                                menus.add(Menu.builder()
                                        .store(store)
                                        .name(title)
                                        .description(description)
                                        .price(priceValue)
                                        .build());
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Failed to fetch menus from Toss API for {}: {}", merchantId, e.getMessage());
        }
        return menus;
    }


    @Transactional
    public SyncResponse updateStoreData(UUID storeId, UUID userId, com.matketing.be.domain.onboarding.dto.StoreUpdateRequest request) {
        Store store = storeRepository.findById(storeId)
                .orElseThrow(() -> new IllegalArgumentException("Store not found"));

        if (!store.getUserId().equals(userId)) {
            throw new IllegalArgumentException("Not authorized to update this store");
        }

        store.updateAllDetails(
                null,
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
        String url = crawlerBaseUrl + "/api/search?keyword=" + keyword;
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                url, HttpMethod.GET, null, new ParameterizedTypeReference<>() {});
        return response.getBody();
    }

    public Map<String, Object> getPlaceDetailViaCrawler(String placeId) {
        String url = crawlerBaseUrl + "/api/place/" + placeId;
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                url, HttpMethod.GET, null, new ParameterizedTypeReference<>() {});
        return response.getBody();
    }
}
