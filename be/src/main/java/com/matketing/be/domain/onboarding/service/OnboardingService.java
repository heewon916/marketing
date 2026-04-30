package com.matketing.be.domain.onboarding.service;

import com.matketing.be.domain.onboarding.dto.PinVerifyResponse;
import com.matketing.be.domain.onboarding.dto.SyncResponse;
import com.matketing.be.domain.onboarding.entity.PosPin;
import com.matketing.be.domain.onboarding.repository.PosPinRepository;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.MenuRepository;
import com.matketing.be.domain.store.repository.StoreHoursRepository;
import com.matketing.be.domain.store.repository.StoreRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class OnboardingService {

    private final PosPinRepository posPinRepository;
    private final StoreRepository storeRepository;
    private final MenuRepository menuRepository;
    private final StoreHoursRepository storeHoursRepository;

    public void registerPin(String pin, String merchantId) {
        // Redis에 난수와 merchantId 저장 (엔티티에 설정된 TTL 3분 자동 적용)
        posPinRepository.save(PosPin.builder()
                .pin(pin)
                .merchantId(merchantId)
                .build());
    }

    public PinVerifyResponse verifyPin(String pin) {
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
    public SyncResponse syncStoreData(UUID userId, String merchantId) {
        log.info("Starting sync for user: {}, merchant: {}", userId, merchantId);

        // 1. Toss OpenAPI 호출하여 상호명, 카테고리 등 기본 정보 및 메뉴 추출 (TODO: 실제 Toss API 연동)
        String storeName = "테스트 매장"; // Toss에서 가져올 정보 Mocking
        String category = "CAFE";
        
        // 2. 내부 FastAPI 크롤러 호출 (장소 검색: /api/search?keyword=storeName)
        // String placeId = callCrawlerSearchApi(storeName);
        String placeId = "123456"; // 크롤러에서 받아올 place_id Mocking

        // 3. 내부 FastAPI 크롤러 호출 (상세 정보: /api/place/{placeId})
        // CrawlerDetailResponse detail = callCrawlerDetailApi(placeId);
        // detail 객체에서 주소, 위경도, 영업시간, 메뉴 리스트 추출

        // 4. DB 엔티티 생성 및 병합 저장 (Store, StoreHours, Menu)
        Store store = Store.builder()
                .userId(userId)
                .merchantId(merchantId)
                .storeName(storeName)
                .category(category)
                .address("서울특별시 강남구 테헤란로 123") // 크롤링 결과 예시
                .build();
        
        store = storeRepository.save(store);

        // TODO: StoreHours 및 Menu 엔티티들을 store와 연관관계 맺어 save() 하는 로직 추가

        log.info("Successfully synced store data for merchantId: {}", merchantId);
        return new SyncResponse(true, "가맹점 정보 동기화 및 DB 저장 완료", store.getId().toString());
    }

    // --- 크롤러 연동 프록시 메서드 ---
    
    @org.springframework.beans.factory.annotation.Value("${FASTAPI_BASE_URL:http://fastapi:8000}")
    private String fastapiBaseUrl;

    public Object searchPlacesViaCrawler(String keyword) {
        org.springframework.web.client.RestTemplate restTemplate = new org.springframework.web.client.RestTemplate();
        String url = fastapiBaseUrl + "/api/search?keyword=" + keyword;
        return restTemplate.getForObject(url, Object.class);
    }

    public Object getPlaceDetailViaCrawler(String placeId) {
        org.springframework.web.client.RestTemplate restTemplate = new org.springframework.web.client.RestTemplate();
        String url = fastapiBaseUrl + "/api/place/" + placeId;
        return restTemplate.getForObject(url, Object.class);
    }
}

