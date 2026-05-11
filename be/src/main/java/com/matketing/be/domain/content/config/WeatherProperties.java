package com.matketing.be.domain.content.config;

import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "weather")
public record WeatherProperties(
        String kmaServiceKey,
        String airKoreaServiceKey,
        String airKoreaAirServiceKey,
        String airKoreaStationServiceKey,
        String kmaForecastBaseUrl,
        String kmaWarningBaseUrl,
        String airKoreaAirBaseUrl,
        String airKoreaStationBaseUrl,
        long cacheTtlSeconds,
        long warningCacheTtlSeconds,
        long stationCacheTtlSeconds
) {

    public WeatherProperties {
        if (kmaForecastBaseUrl == null || kmaForecastBaseUrl.isBlank()) {
            kmaForecastBaseUrl = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0";
        }
        if (kmaWarningBaseUrl == null || kmaWarningBaseUrl.isBlank()) {
            kmaWarningBaseUrl = "http://apis.data.go.kr/1360000/WthrWrnInfoService";
        }
        if (airKoreaAirBaseUrl == null || airKoreaAirBaseUrl.isBlank()) {
            airKoreaAirBaseUrl = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc";
        }
        if (airKoreaStationBaseUrl == null || airKoreaStationBaseUrl.isBlank()) {
            airKoreaStationBaseUrl = "http://apis.data.go.kr/B552584/MsrstnInfoInqireSvc";
        }
        if (cacheTtlSeconds <= 0) {
            cacheTtlSeconds = 2400;
        }
        if (warningCacheTtlSeconds <= 0) {
            warningCacheTtlSeconds = 600;
        }
        if (stationCacheTtlSeconds <= 0) {
            stationCacheTtlSeconds = 86400;
        }
    }

    public String kmaServiceKeyForQuery() {
        return decodeIfEncoded(kmaServiceKey);
    }

    public String airKoreaServiceKeyForQuery() {
        return decodeIfEncoded(airKoreaServiceKey);
    }

    public boolean hasAirKoreaAirServiceKey() {
        return hasText(resolvedAirKoreaAirServiceKey());
    }

    public boolean hasAirKoreaStationServiceKey() {
        return hasText(resolvedAirKoreaStationServiceKey());
    }

    public String airKoreaAirServiceKeyForQuery() {
        return decodeIfEncoded(resolvedAirKoreaAirServiceKey());
    }

    public String airKoreaStationServiceKeyForQuery() {
        return decodeIfEncoded(resolvedAirKoreaStationServiceKey());
    }

    private String resolvedAirKoreaAirServiceKey() {
        return firstNonBlank(airKoreaAirServiceKey, airKoreaServiceKey);
    }

    private String resolvedAirKoreaStationServiceKey() {
        return firstNonBlank(airKoreaStationServiceKey, airKoreaServiceKey);
    }

    private String firstNonBlank(String primary, String fallback) {
        return hasText(primary) ? primary : fallback;
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    private String decodeIfEncoded(String value) {
        if (value == null || !value.contains("%")) {
            return value;
        }
        return URLDecoder.decode(value, StandardCharsets.UTF_8);
    }
}
