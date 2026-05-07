package com.matketing.be.domain.content.client;

import com.matketing.be.domain.content.config.WeatherProperties;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Slf4j
@Component
public class KmaWarningClient {

    private final RestClient restClient;
    private final WeatherProperties properties;

    public KmaWarningClient(RestClient.Builder builder, WeatherProperties properties) {
        this.restClient = builder.baseUrl(properties.kmaWarningBaseUrl()).build();
        this.properties = properties;
    }

    /**
     * [기상청 기상특보 조회]
     * - getPwnStatus 응답의 t6, t7, t1, t2, t4 문자열을 검사한다.
     * - 매장 주소에서 추출한 시도/시군구가 특보 문자열에 포함될 때만 반영한다.
     * - 호우/태풍 특보가 없거나 지역 매칭이 불명확하면 null 값 DTO를 반환한다.
     * @param address 매장 주소
     * @return 호우/태풍 특보 정보
     */
    public WarningData getWarnings(String address) {
        if (properties.kmaServiceKey() == null || properties.kmaServiceKey().isBlank()) {
            log.warn("weather.kma.warning-skipped: KMA_SERVICE_KEY is empty");
            return WarningData.empty();
        }

        Region region = Region.from(address);
        if (region.isEmpty()) {
            log.warn("weather.kma.warning-region-unmatched: address={}", address);
            return WarningData.empty();
        }

        try {
            Map<String, Object> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder.path("/getPwnStatus")
                            .queryParam("serviceKey", properties.kmaServiceKeyForQuery())
                            .queryParam("numOfRows", 10)
                            .queryParam("pageNo", 1)
                            .queryParam("dataType", "JSON")
                            .build())
                    .retrieve()
                    .body(Map.class);

            if (!isSuccess(response)) {
                log.warn("weather.kma.warning-failed: non-success result. address={}", address);
                return WarningData.empty();
            }

            String heavyRainWarning = null;
            String typhoonWarning = null;
            for (Map<String, Object> item : items(response)) {
                // 특보 문구가 여러 필드에 나뉘어 내려오므로 후보 필드를 모두 순회한다.
                for (String key : List.of("t6", "t7", "t1", "t2", "t4")) {
                    String text = stringValue(item.get(key));
                    if (text == null || text.isBlank()) {
                        continue;
                    }
                    if (!region.matches(text)) {
                        continue;
                    }
                    // 한 지역에 여러 문구가 있을 수 있으므로 필요한 특보가 처음 발견된 값만 저장한다.
                    if (heavyRainWarning == null) {
                        heavyRainWarning = firstContaining(text, "호우경보", "호우주의보");
                    }
                    if (typhoonWarning == null) {
                        typhoonWarning = firstContaining(text, "태풍경보", "태풍주의보");
                    }
                }
            }
            return new WarningData(heavyRainWarning, typhoonWarning);
        } catch (RestClientException exception) {
            log.warn("weather.kma.warning-failed: request failed. address={}", address, exception);
            return WarningData.empty();
        } catch (Exception exception) {
            log.warn("weather.kma.warning-failed: response parsing failed. address={}", address, exception);
            return WarningData.empty();
        }
    }

    // 특보 문자열 안에서 요구한 경보/주의보 키워드가 있는지 확인한다.
    private String firstContaining(String text, String... warnings) {
        for (String warning : warnings) {
            if (text.contains(warning)) {
                return warning;
            }
        }
        return null;
    }

    private boolean isSuccess(Map<String, Object> response) {
        String resultCode = stringValue(header(response).get("resultCode"));
        return "00".equals(resultCode) || "0".equals(resultCode);
    }

    private Map<String, Object> header(Map<String, Object> response) {
        return mapValue(mapValue(response.get("response")).get("header"));
    }

    private List<Map<String, Object>> items(Map<String, Object> response) {
        Object item = mapValue(mapValue(mapValue(response.get("response")).get("body")).get("items")).get("item");
        if (item instanceof List<?> list) {
            return list.stream()
                    .filter(Map.class::isInstance)
                    .map(value -> (Map<String, Object>) value)
                    .toList();
        }
        if (item instanceof Map<?, ?> map) {
            return List.of((Map<String, Object>) map);
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

    private record Region(String sido, String sigungu) {
        // 주소 앞부분에서 시도/시군구만 추출한다. 상세 주소는 특보 지역 매칭에 사용하지 않는다.
        static Region from(String address) {
            if (address == null || address.isBlank()) {
                return new Region(null, null);
            }
            String[] tokens = address.trim().split("\\s+");
            String sido = tokens.length > 0 ? normalizeSido(tokens[0]) : null;
            String sigungu = tokens.length > 1 ? tokens[1] : null;
            return new Region(sido, sigungu);
        }

        boolean isEmpty() {
            return sido == null && sigungu == null;
        }

        // 시군구가 매칭되면 가장 신뢰도가 높고, 시도 단위 특보도 반영할 수 있게 시도 매칭을 보조로 허용한다.
        boolean matches(String text) {
            boolean sidoMatches = sido != null && text.contains(sido);
            boolean sigunguMatches = sigungu != null && text.contains(sigungu);
            return sigunguMatches || sidoMatches;
        }

        // 특보 문자열은 보통 축약 시도명으로 내려오므로 행정구역 정식명을 축약명으로 맞춘다.
        private static String normalizeSido(String value) {
            if (value == null) {
                return null;
            }
            return switch (value) {
                case "서울특별시" -> "서울";
                case "부산광역시" -> "부산";
                case "대구광역시" -> "대구";
                case "인천광역시" -> "인천";
                case "광주광역시" -> "광주";
                case "대전광역시" -> "대전";
                case "울산광역시" -> "울산";
                case "세종특별자치시" -> "세종";
                case "경기도" -> "경기";
                case "강원특별자치도", "강원도" -> "강원";
                case "충청북도" -> "충북";
                case "충청남도" -> "충남";
                case "전북특별자치도", "전라북도" -> "전북";
                case "전라남도" -> "전남";
                case "경상북도" -> "경북";
                case "경상남도" -> "경남";
                case "제주특별자치도" -> "제주";
                default -> value;
            };
        }
    }

    public record WarningData(String heavyRainWarning, String typhoonWarning) {
        public static WarningData empty() {
            return new WarningData(null, null);
        }
    }
}
