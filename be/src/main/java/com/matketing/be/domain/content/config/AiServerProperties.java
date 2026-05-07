package com.matketing.be.domain.content.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "ai.server")
public record AiServerProperties(
        String baseUrl,
        long timeoutSeconds
) {
    public AiServerProperties {
        if (baseUrl == null || baseUrl.isBlank()) {
            baseUrl = "http://fastapi:8000";
        }
        if (timeoutSeconds <= 0) {
            timeoutSeconds = 10;
        }
    }
}
