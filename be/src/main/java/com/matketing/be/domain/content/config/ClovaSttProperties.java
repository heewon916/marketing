package com.matketing.be.domain.content.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "clova.stt")
public record ClovaSttProperties(
        String baseUrl,
        String secretKey,
        long timeoutSeconds
) {
    public ClovaSttProperties {
        if (timeoutSeconds <= 0) {
            timeoutSeconds = 10;
        }
    }
}
