package com.matketing.be.domain.user.entity;

import lombok.Builder;
import lombok.Getter;
import org.springframework.data.annotation.Id;
import org.springframework.data.redis.core.RedisHash;

@Getter
@RedisHash(value = "refreshToken", timeToLive = 1209600) // 14일 = 1209600초
public class RefreshToken {

    @Id
    private String id; // instagramUserId 또는 유저 식별자
    
    private String refreshToken;

    @Builder
    public RefreshToken(String id, String refreshToken) {
        this.id = id;
        this.refreshToken = refreshToken;
    }
}
