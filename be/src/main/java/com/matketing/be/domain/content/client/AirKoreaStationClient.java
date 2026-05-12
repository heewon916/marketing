package com.matketing.be.domain.content.client;

import com.matketing.be.domain.content.config.WeatherProperties;
import com.matketing.be.domain.content.util.HaversineDistanceCalculator;
import com.matketing.be.domain.content.util.WeatherValueParser;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Slf4j
@Component
public class AirKoreaStationClient {

    public static final List<String> SUPPORTED_SIDOS = List.of(
            "서울",
            "부산",
            "대구",
            "인천",
            "광주",
            "대전",
            "울산",
            "세종",
            "경기",
            "강원",
            "충북",
            "충남",
            "전북",
            "전남",
            "경북",
            "경남",
            "제주"
    );

    private final RestClient restClient;
    private final WeatherProperties properties;

    public AirKoreaStationClient(RestClient.Builder builder, WeatherProperties properties) {
        this.restClient = builder.baseUrl(properties.airKoreaStationBaseUrl()).build();
        this.properties = properties;
    }

    /**
     * [에어코리아 측정소 목록 조회]
     * - 대기오염정보 API는 stationName이 필요하므로, 먼저 시도(addr) 기준 측정소 목록을 가져온다.
     * - ver=1.1 기준 dmX는 경도, dmY는 위도이므로 Station DTO에 그대로 매핑한다.
     * - 외부 API 실패 시 게시글 생성을 막지 않도록 빈 목록을 반환한다.
     * @param sido 주소에서 추출한 시도명
     * @return 측정소 목록
     */
    public List<Station> getStations(String sido) {
        if (!properties.hasAirKoreaStationServiceKey()) {
            log.warn("weather.airkorea.station-skipped: AIRKOREA_STATION_SERVICE_KEY is empty");
            return List.of();
        }

        try {
            Map<String, Object> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder.path("/getMsrstnList")
                            .queryParam("serviceKey", properties.airKoreaStationServiceKeyForQuery())
                            .queryParam("returnType", "json")
                            .queryParam("numOfRows", 1000)
                            .queryParam("pageNo", 1)
                            .queryParam("addr", sido)
                            .queryParam("ver", "1.1")
                            .build())
                    .retrieve()
                    .body(Map.class);

            if (!isSuccess(response)) {
                log.warn("weather.airkorea.station-failed: non-success result. sido={}", sido);
                return List.of();
            }

            return items(response).stream()
                    // stationName과 좌표가 모두 있는 측정소만 거리 계산 후보로 사용한다.
                    .map(item -> new Station(
                            stringValue(item.get("stationName")),
                            stringValue(item.get("addr")),
                            WeatherValueParser.parseDouble(stringValue(item.get("dmX"))),
                            WeatherValueParser.parseDouble(stringValue(item.get("dmY")))
                    ))
                    .filter(station -> station.stationName() != null && station.longitude() != null && station.latitude() != null)
                    .toList();
        } catch (RestClientException exception) {
            log.warn("weather.airkorea.station-failed: request failed. sido={}", sido, exception);
            return List.of();
        } catch (Exception exception) {
            log.warn("weather.airkorea.station-failed: response parsing failed. sido={}", sido, exception);
            return List.of();
        }
    }

    /**
     * [가장 가까운 측정소 선택]
     * - 매장 좌표와 측정소 좌표 사이의 Haversine 거리를 비교한다.
     * - 가장 짧은 거리의 stationName을 이후 대기질 조회에 사용한다.
     * @param stations 측정소 목록
     * @param storeLongitude 매장 경도
     * @param storeLatitude 매장 위도
     * @return 가장 가까운 측정소
     */
    public Station nearestStation(List<Station> stations, double storeLongitude, double storeLatitude) {
        Station nearest = null;
        double nearestDistance = Double.MAX_VALUE;
        for (Station station : stations) {
            double distance = HaversineDistanceCalculator.distanceKm(storeLongitude, storeLatitude, station.longitude(), station.latitude());
            if (distance < nearestDistance) {
                nearest = station;
                nearestDistance = distance;
            }
        }
        return nearest;
    }

    /**
     * 주소에서 에어코리아 addr 파라미터에 사용할 시도명을 추출한다.
     * @param address 매장 주소
     * @return 축약 시도명
     */
    public static String extractSido(String address) {
        if (address == null || address.isBlank()) {
            return null;
        }
        String first = address.trim().split("\\s+")[0];
        return switch (first) {
            case "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
                 "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주" -> first;
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
            default -> null;
        };
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

    public record Station(String stationName, String address, Double longitude, Double latitude) {
    }
}
