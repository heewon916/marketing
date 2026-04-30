package com.matketing.be.domain.onboarding.service;

import com.matketing.be.domain.onboarding.dto.PinVerifyResponse;
import com.matketing.be.domain.onboarding.entity.PosPin;
import com.matketing.be.domain.onboarding.repository.PosPinRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class OnboardingService {

    private final PosPinRepository posPinRepository;

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
}
