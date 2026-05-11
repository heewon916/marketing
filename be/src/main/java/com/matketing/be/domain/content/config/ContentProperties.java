package com.matketing.be.domain.content.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "content")
public record ContentProperties(
        long idempotencyTtlSeconds
) {
    public ContentProperties {
        if (idempotencyTtlSeconds <= 0) {
            idempotencyTtlSeconds = 600; // 10분
        }
    }
}
