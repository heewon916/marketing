package com.matketing.be.domain.content.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "clova.stt")
public record ClovaSttProperties(
        String baseUrl,
        String secretKey,
        String lang,
        boolean assessment,
        String utterance,
        String boostings,
        boolean graph,
        String ffmpegPath,
        long timeoutSeconds
) {
    public ClovaSttProperties {
        if (baseUrl == null || baseUrl.isBlank()) {
            baseUrl = "https://clovaspeech-gw.ncloud.com/recog/v1";
        }
        if (lang == null || lang.isBlank()) {
            lang = "Kor";
        }
        if (ffmpegPath == null || ffmpegPath.isBlank()) {
            ffmpegPath = "ffmpeg";
        }
        if (timeoutSeconds <= 0) {
            timeoutSeconds = 10;
        }
    }
}
