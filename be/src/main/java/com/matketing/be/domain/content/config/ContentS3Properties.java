package com.matketing.be.domain.content.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "content.s3")
public record ContentS3Properties(
        String bucketName,
        String region,
        String publicBaseUrl
) {
}
