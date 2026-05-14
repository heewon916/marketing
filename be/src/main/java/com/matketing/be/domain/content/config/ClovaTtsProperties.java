package com.matketing.be.domain.content.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "clova.tts")
public record ClovaTtsProperties(
        String baseUrl,
        String clientId,
        String clientSecret,
        String speaker,
        long timeoutSeconds
) {
    public ClovaTtsProperties {
        if (baseUrl == null || baseUrl.isBlank()) {
            baseUrl = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts";
        }
        if (speaker == null || speaker.isBlank()) {
            speaker = "ndain"; // 기본 목소리
        }
        if (timeoutSeconds <= 0) {
            timeoutSeconds = 10;
        }
    }
}
