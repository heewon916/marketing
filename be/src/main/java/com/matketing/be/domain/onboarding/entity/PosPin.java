package com.matketing.be.domain.onboarding.entity;

import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.redis.core.RedisHash;

@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@RedisHash(value = "posPin", timeToLive = 180) // 3분 = 180초 TTL
public class PosPin {

    @Id
    private String pin; // 6자리 난수

    private String merchantId; // 토스 가맹점 식별자 (6자리 숫자)

    @Builder
    public PosPin(String pin, String merchantId) {
        this.pin = pin;
        this.merchantId = merchantId;
    }
}
