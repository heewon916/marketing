package com.matketing.be.domain.content.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;

@Slf4j
@Configuration
@EnableConfigurationProperties(ContentS3Properties.class)
public class S3Config {

    @Bean
    public S3Client s3Client(ContentS3Properties properties) {
        boolean hasAccessKey = properties.accessKey() != null && !properties.accessKey().isBlank();
        boolean hasSecretKey = properties.secretKey() != null && !properties.secretKey().isBlank();
        
        log.info("[S3Config] bucket={}, region={}, accessKeyPresent={}, secretKeyPresent={}, cloudfrontDomain={}, credentialsProvider={}",
                properties.bucketName(),
                properties.region(),
                hasAccessKey,
                hasSecretKey,
                properties.publicBaseUrl(),
                hasAccessKey && hasSecretKey ? "StaticCredentialsProvider" : "DefaultCredentialsProvider");

        var builder = S3Client.builder()
                .region(Region.of(properties.region()));

        if (hasAccessKey && hasSecretKey) {
            builder.credentialsProvider(StaticCredentialsProvider.create(
                    AwsBasicCredentials.create(properties.accessKey(), properties.secretKey())
            ));
        }

        return builder.build();
    }
}
