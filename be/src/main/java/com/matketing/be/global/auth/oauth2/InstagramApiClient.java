package com.matketing.be.global.auth.oauth2;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@Component
public class InstagramApiClient {

    private final String clientSecret;
    private final RestTemplate restTemplate;

    public InstagramApiClient(
            @Value("${spring.security.oauth2.client.registration.instagram.client-secret}") String clientSecret) {
        this.clientSecret = clientSecret;
        this.restTemplate = new RestTemplate();
    }

    /**
     * 장기 토큰을 장기 토큰으로 교환합니다.
     * @param shortLivedToken 단기 토큰
     * @return 장기 토큰 정보가 담긴 Map (성공 시), 실패 시 null
     */
    public Map<String, Object> exchangeForLongLivedToken(String shortLivedToken) {
        try {
            String url = String.format(
                    "https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=%s&access_token=%s",
                    clientSecret, shortLivedToken
            );
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> body = (Map<String, Object>) response.getBody();
                log.info("Successfully exchanged for Instagram long-lived token.");
                return body;
            }
        } catch (Exception e) {
            log.error("Failed to exchange Instagram token for long-lived token: {}", e.getMessage());
        }
        return null; // 교환 실패 시 null 반환
    }

    /**
     * Instagram Graph API를 호출하여 유저 프로필 정보를 가져옵니다.
     */
    public Map<String, Object> getUserProfile(String accessToken) {
        try {
            String url = String.format(
                    "https://graph.instagram.com/me?fields=id,username,profile_picture_url&access_token=%s",
                    accessToken
            );
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                return (Map<String, Object>) response.getBody();
            }
        } catch (Exception e) {
            log.error("Failed to fetch Instagram profile: {}", e.getMessage());
            try {
                String url = String.format(
                        "https://graph.instagram.com/me?fields=id,username&access_token=%s",
                        accessToken
                );
                ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    return (Map<String, Object>) response.getBody();
                }
            } catch (Exception ex) {
                log.error("Failed to fetch Instagram profile (fallback): {}", ex.getMessage());
            }
        }
        return null;
    }
}
