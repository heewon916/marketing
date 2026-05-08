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
        // 특보 API 전용 baseUrl을 가진 RestClient를 만들어 다른 기상 API 설정과 분리한다.
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
        // 운영 환경에서 서비스키가 빠진 경우에도 게시글 생성 흐름이 중단되지 않도록 빈 특보로 처리한다.
        if (properties.kmaServiceKey() == null || properties.kmaServiceKey().isBlank()) {
            log.warn("weather.kma.warning-skipped: KMA_SERVICE_KEY is empty");
            return WarningData.empty();
        }

        // 기상청 특보 응답은 전국 특보 문장을 내려주기 때문에, 먼저 매장 주소에서 비교할 지역명을 뽑는다.
        Region region = Region.from(address);
        if (region.isEmpty()) {
            log.warn("weather.kma.warning-region-unmatched: address={}", address);
            return WarningData.empty();
        }

        try {
            // getPwnStatus는 현재 발표 중인 기상특보 현황을 조회한다.
            // serviceKeyForQuery()는 URL 인코딩 여부 차이를 WeatherProperties 쪽에서 정리한 값이다.
            Map<String, Object> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder.path("/getPwnStatus")
                            .queryParam("serviceKey", properties.kmaServiceKeyForQuery())
                            .queryParam("numOfRows", 10)
                            .queryParam("pageNo", 1)
                            .queryParam("dataType", "JSON")
                            .build())
                    .retrieve()
                    .body(Map.class);

            // 기상청 OpenAPI는 HTTP 200이어도 header.resultCode로 업무 성공/실패를 따로 알려준다.
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
                    // 경보와 주의보가 동시에 잡히면 인자로 먼저 넣은 경보를 우선한다.
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
        // 일부 공공데이터 응답은 성공 코드를 "00" 또는 "0"으로 내려줄 수 있어 둘 다 허용한다.
        String resultCode = stringValue(header(response).get("resultCode"));
        return "00".equals(resultCode) || "0".equals(resultCode);
    }

    private Map<String, Object> header(Map<String, Object> response) {
        // response.header가 없거나 형식이 달라도 mapValue가 빈 Map으로 바꿔 예외를 막는다.
        return mapValue(mapValue(response.get("response")).get("header"));
    }

    private List<Map<String, Object>> items(Map<String, Object> response) {
        // 기상청 응답은 item이 1건이면 객체, 여러 건이면 배열로 내려올 수 있어 두 형태를 모두 처리한다.
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
        // 외부 API 응답 구조가 예상과 달라도 호출부에서 NullPointerException이 나지 않도록 빈 Map을 반환한다.
        if (value instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Map.of();
    }

    private String stringValue(Object value) {
        // 숫자 코드처럼 문자열이 아닌 값도 contains/equals 비교에 쓸 수 있게 문자열로 통일한다.
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
            // 주소가 없거나 공백이면 특보 문장과 비교할 기준이 없다.
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
