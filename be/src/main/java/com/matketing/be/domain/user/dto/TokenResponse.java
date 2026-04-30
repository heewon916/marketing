package com.matketing.be.domain.user.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class TokenResponse {
    private String accessToken;
    
    @JsonProperty("token_expires_at")
    private String tokenExpiresAt;
}
