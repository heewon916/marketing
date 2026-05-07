package com.matketing.be.domain.content.client;

import com.matketing.be.domain.content.config.WeatherProperties;
import com.matketing.be.domain.content.util.WeatherValueParser;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Slf4j
@Component
public class AirKoreaAirQualityClient {

    private static final Set<String> INVALID_FLAGS = Set.of("점검및교정", "장비점검", "자료이상", "통신장애");

    private final RestClient restClient;
    private final WeatherProperties properties;

    public AirKoreaAirQualityClient(RestClient.Builder builder, WeatherProperties properties) {
        this.restClient = builder.baseUrl(properties.airKoreaAirBaseUrl()).build();
        this.properties = properties;
    }

    /**
     * [측정소별 실시간 대기질 조회]
     * - 가까운 측정소 stationName으로 DAILY 범위의 최신 측정값 목록을 조회한다.
     * - dataTime 최신순으로 정렬한 뒤 PM10/PM2.5 각각의 첫 유효값을 선택한다.
     * - 값이 없거나 점검/통신장애 플래그가 있으면 null로 둔다.
     * @param stationName 에어코리아 측정소명
     * @return PM10/PM2.5 값
     */
    public AirQualityData getAirQuality(String stationName) {
        if (properties.airKoreaServiceKey() == null || properties.airKoreaServiceKey().isBlank()) {
            log.warn("weather.airkorea.air-skipped: AIRKOREA_SERVICE_KEY is empty");
            return AirQualityData.empty();
        }
        if (stationName == null || stationName.isBlank()) {
            return AirQualityData.empty();
        }

        try {
            Map<String, Object> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder.path("/getMsrstnAcctoRltmMesureDnsty")
                            .queryParam("serviceKey", properties.airKoreaServiceKeyForQuery())
                            .queryParam("returnType", "json")
                            .queryParam("numOfRows", 100)
                            .queryParam("pageNo", 1)
                            .queryParam("stationName", stationName)
                            .queryParam("dataTerm", "DAILY")
                            .queryParam("ver", "1.5")
                            .build())
                    .retrieve()
                    .body(Map.class);

            if (!isSuccess(response)) {
                log.warn("weather.airkorea.air-failed: non-success result. stationName={}", stationName);
                return AirQualityData.empty();
            }

            Integer pm10 = null;
            Integer pm25 = null;
            for (Map<String, Object> item : items(response).stream()
                    // 최신 측정값부터 검사해 유효한 값을 최대한 빠르게 찾는다.
                    .sorted(Comparator.comparing((Map<String, Object> item) -> stringValue(item.get("dataTime")), Comparator.nullsLast(String::compareTo)).reversed())
                    .toList()) {
                if (pm10 == null && isValid(item, "pm10Value", "pm10Flag")) {
                    pm10 = WeatherValueParser.parseInteger(stringValue(item.get("pm10Value")));
                }
                if (pm25 == null && isValid(item, "pm25Value", "pm25Flag")) {
                    pm25 = WeatherValueParser.parseInteger(stringValue(item.get("pm25Value")));
                }
                if (pm10 != null && pm25 != null) {
                    break;
                }
            }
            return new AirQualityData(pm10, pm25);
        } catch (RestClientException exception) {
            log.warn("weather.airkorea.air-failed: request failed. stationName={}", stationName, exception);
            return AirQualityData.empty();
        } catch (Exception exception) {
            log.warn("weather.airkorea.air-failed: response parsing failed. stationName={}", stationName, exception);
            return AirQualityData.empty();
        }
    }

    /**
     * PM10/PM2.5 측정값 유효성 검사.
     * - "-", 빈 값, 숫자 파싱 불가 값은 무효다.
     * - 점검/자료이상/통신장애 플래그가 있으면 값이 있어도 무효다.
     * @param value 측정값 문자열
     * @param flag 측정 상태 플래그
     * @return 사용할 수 있는 측정값이면 true
     */
    public static boolean isValidAirValue(String value, String flag) {
        return value != null
                && !value.isBlank()
                && !"-".equals(value.trim())
                && (flag == null || flag.isBlank() || !INVALID_FLAGS.contains(flag.trim()))
                && WeatherValueParser.parseInteger(value) != null;
    }

    private boolean isValid(Map<String, Object> item, String valueKey, String flagKey) {
        return isValidAirValue(stringValue(item.get(valueKey)), stringValue(item.get(flagKey)));
    }

    // 에어코리아 응답은 서비스별로 header.resultCode 또는 response.resultCode 형태가 섞일 수 있어 둘 다 확인한다.
    private boolean isSuccess(Map<String, Object> response) {
        Map<String, Object> responseBody = mapValue(response.get("response"));
        String resultCode = stringValue(mapValue(responseBody.get("header")).get("resultCode"));
        if (resultCode == null) {
            resultCode = stringValue(responseBody.get("resultCode"));
        }
        return "00".equals(resultCode) || "0".equals(resultCode);
    }

    private List<Map<String, Object>> items(Map<String, Object> response) {
        Object item = mapValue(mapValue(response.get("response")).get("body")).get("items");
        if (item instanceof List<?> list) {
            return list.stream()
                    .filter(Map.class::isInstance)
                    .map(value -> (Map<String, Object>) value)
                    .toList();
        }
        return List.of();
    }

    private Map<String, Object> mapValue(Object value) {
        if (value instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Map.of();
    }

    private String stringValue(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    public record AirQualityData(Integer pm10, Integer pm25) {
        public static AirQualityData empty() {
            return new AirQualityData(null, null);
        }
    }
}
