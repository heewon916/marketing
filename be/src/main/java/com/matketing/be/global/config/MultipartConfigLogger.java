package com.matketing.be.global.config;

import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.web.servlet.MultipartProperties;
import org.springframework.context.annotation.Configuration;

@Slf4j
@Configuration
@RequiredArgsConstructor
public class MultipartConfigLogger {

    private final MultipartProperties multipartProperties;

    @PostConstruct
    public void logMultipartProperties() {
        log.info("=================================================");
        log.info("Multipart Configuration:");
        log.info("Max File Size: {}", multipartProperties.getMaxFileSize());
        log.info("Max Request Size: {}", multipartProperties.getMaxRequestSize());
        log.info("=================================================");
    }
}
