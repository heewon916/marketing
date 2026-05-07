package com.matketing.be.domain.content.client;

import com.matketing.be.domain.content.config.WeatherProperties;
import com.matketing.be.domain.content.util.WeatherValueParser;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Slf4j
@Component
public class KmaForecastClient {

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final List<String> VILAGE_BASE_TIMES = List.of("0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300");

    private final RestClient restClient;
    private final WeatherProperties properties;

    public KmaForecastClient(RestClient.Builder builder, WeatherProperties properties) {
        this.restClient = builder.baseUrl(properties.kmaForecastBaseUrl()).build();
        this.properties = properties;
    }

    /**
     * [기상청 초단기실황 조회]
     * - 현재 기온(T1H), 1시간 강수량(RN1), 습도(REH), 풍속(WSD)을 조회한다.
     * - 초단기실황은 매시각 10분 이후 제공되므로, 현재 분이 10분 미만이면 직전 시간을 base_time으로 사용한다.
     * - 외부 API 실패 또는 resultCode 실패 시 게시글 생성을 막지 않도록 빈 DTO를 반환한다.
     * @param now 조회 기준 시각
     * @param nx 기상청 격자 X
     * @param ny 기상청 격자 Y
     * @return 실황 날씨 값
     */
    public UltraSrtNcstData getUltraSrtNcst(LocalDateTime now, int nx, int ny) {
        if (properties.kmaServiceKey() == null || properties.kmaServiceKey().isBlank()) {
            log.warn("weather.kma.ultra-skipped: KMA_SERVICE_KEY is empty");
            return UltraSrtNcstData.empty();
        }

        // 발표 가능 시각을 고려해 base_date/base_time을 계산한다.
        LocalDateTime base = now.getMinute() < 10 ? now.minusHours(1) : now;
        String baseDate = base.format(DATE_FORMATTER);
        String baseTime = "%02d00".formatted(base.getHour());

        try {
            Map<String, Object> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder.path("/getUltraSrtNcst")
                            .queryParam("serviceKey", properties.kmaServiceKeyForQuery())
                            .queryParam("numOfRows", 100)
                            .queryParam("pageNo", 1)
                            .queryParam("dataType", "JSON")
                            .queryParam("base_date", baseDate)
                            .queryParam("base_time", baseTime)
                            .queryParam("nx", nx)
                            .queryParam("ny", ny)
                            .build())
                    .retrieve()
                    .body(Map.class);

            if (!isSuccess(response)) {
                log.warn("weather.kma.ultra-failed: non-success result. nx={}, ny={}, baseDate={}, baseTime={}", nx, ny, baseDate, baseTime);
                return UltraSrtNcstData.empty();
            }

            Double temperature = null;
            Double precipitation = null;
            Integer humidity = null;
            Double windSpeed = null;
            for (Map<String, Object> item : items(response)) {
                // category별 obsrValue를 내부 weather 필드 타입에 맞춰 변환한다.
                String category = stringValue(item.get("category"));
                String value = stringValue(item.get("obsrValue"));
                switch (category) {
                    case "T1H" -> temperature = WeatherValueParser.parseDouble(value);
                    case "RN1" -> precipitation = WeatherValueParser.parsePrecipitation(value);
                    case "REH" -> humidity = WeatherValueParser.parseInteger(value);
                    case "WSD" -> windSpeed = WeatherValueParser.parseDouble(value);
                    default -> {
                    }
                }
            }
            return new UltraSrtNcstData(temperature, precipitation, humidity, windSpeed);
        } catch (RestClientException exception) {
            log.warn("weather.kma.ultra-failed: request failed. nx={}, ny={}", nx, ny, exception);
            return UltraSrtNcstData.empty();
        } catch (Exception exception) {
            log.warn("weather.kma.ultra-failed: response parsing failed. nx={}, ny={}", nx, ny, exception);
            return UltraSrtNcstData.empty();
        }
    }

    /**
     * [기상청 단기예보 조회]
     * - 하늘상태(SKY), 최저/최고기온(TMN/TMX), 시간별 기온(TMP), 예보 fallback 값을 조회한다.
     * - 단기예보 발표시각 후보 중 현재 시각 이전의 가장 최근 발표시각을 base_time으로 사용한다.
     * - TMN/TMX가 없으면 TMP 목록의 최대/최소값으로 일교차를 계산한다.
     * @param now 조회 기준 시각
     * @param nx 기상청 격자 X
     * @param ny 기상청 격자 Y
     * @return 예보 기반 날씨 값
     */
    public VilageFcstData getVilageFcst(LocalDateTime now, int nx, int ny) {
        if (properties.kmaServiceKey() == null || properties.kmaServiceKey().isBlank()) {
            log.warn("weather.kma.vilage-skipped: KMA_SERVICE_KEY is empty");
            return VilageFcstData.empty();
        }

        BaseDateTime base = latestVilageBaseDateTime(now);
        try {
            Map<String, Object> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder.path("/getVilageFcst")
                            .queryParam("serviceKey", properties.kmaServiceKeyForQuery())
                            .queryParam("numOfRows", 1000)
                            .queryParam("pageNo", 1)
                            .queryParam("dataType", "JSON")
                            .queryParam("base_date", base.date())
                            .queryParam("base_time", base.time())
                            .queryParam("nx", nx)
                            .queryParam("ny", ny)
                            .build())
                    .retrieve()
                    .body(Map.class);

            if (!isSuccess(response)) {
                log.warn("weather.kma.vilage-failed: non-success result. nx={}, ny={}, baseDate={}, baseTime={}", nx, ny, base.date(), base.time());
                return VilageFcstData.empty();
            }

            String cloudCover = null;
            Double minTemperature = null;
            Double maxTemperature = null;
            Double precipitation = null;
            Integer humidity = null;
            Double windSpeed = null;
            Double tmpMin = null;
            Double tmpMax = null;
            String today = now.format(DATE_FORMATTER);

            for (Map<String, Object> item : items(response)) {
                // 오늘 날짜 예보만 사용해 date 필드와 weather 컨텍스트 기준일을 맞춘다.
                String forecastDate = stringValue(item.get("fcstDate"));
                if (!today.equals(forecastDate)) {
                    continue;
                }
                String category = stringValue(item.get("category"));
                String value = stringValue(item.get("fcstValue"));
                switch (category) {
                    case "SKY" -> cloudCover = cloudCover == null ? WeatherValueParser.convertSky(value) : cloudCover;
                    case "TMN" -> minTemperature = WeatherValueParser.parseDouble(value);
                    case "TMX" -> maxTemperature = WeatherValueParser.parseDouble(value);
                    case "TMP" -> {
                        Double tmp = WeatherValueParser.parseDouble(value);
                        if (tmp != null) {
                            tmpMin = tmpMin == null ? tmp : Math.min(tmpMin, tmp);
                            tmpMax = tmpMax == null ? tmp : Math.max(tmpMax, tmp);
                        }
                    }
                    case "PCP" -> precipitation = precipitation == null ? WeatherValueParser.parsePrecipitation(value) : precipitation;
                    case "REH" -> humidity = humidity == null ? WeatherValueParser.parseInteger(value) : humidity;
                    case "WSD" -> windSpeed = windSpeed == null ? WeatherValueParser.parseDouble(value) : windSpeed;
                    default -> {
                    }
                }
            }
            Double diurnalRange = calculateDiurnalRange(minTemperature, maxTemperature, tmpMin, tmpMax);
            return new VilageFcstData(cloudCover, precipitation, humidity, windSpeed, diurnalRange);
        } catch (RestClientException exception) {
            log.warn("weather.kma.vilage-failed: request failed. nx={}, ny={}", nx, ny, exception);
            return VilageFcstData.empty();
        } catch (Exception exception) {
            log.warn("weather.kma.vilage-failed: response parsing failed. nx={}, ny={}", nx, ny, exception);
            return VilageFcstData.empty();
        }
    }

    // 기본은 TMX - TMN이고, 두 값 중 하나라도 없으면 TMP 시간별 목록의 max - min으로 보완한다.
    private Double calculateDiurnalRange(Double minTemperature, Double maxTemperature, Double tmpMin, Double tmpMax) {
        if (minTemperature != null && maxTemperature != null) {
            return Math.round((maxTemperature - minTemperature) * 10.0) / 10.0;
        }
        if (tmpMin != null && tmpMax != null) {
            return Math.round((tmpMax - tmpMin) * 10.0) / 10.0;
        }
        return null;
    }

    // 단기예보 발표시각 후보 중 현재 시각보다 늦지 않은 가장 최근 시간을 찾는다.
    private BaseDateTime latestVilageBaseDateTime(LocalDateTime now) {
        String current = "%02d%02d".formatted(now.getHour(), now.getMinute());
        Optional<String> latest = VILAGE_BASE_TIMES.stream()
                .filter(baseTime -> baseTime.compareTo(current) <= 0)
                .reduce((first, second) -> second);
        if (latest.isPresent()) {
            return new BaseDateTime(now.format(DATE_FORMATTER), latest.get());
        }
        LocalDateTime yesterday = now.minusDays(1);
        return new BaseDateTime(yesterday.format(DATE_FORMATTER), "2300");
    }

    // 공공데이터포털 API는 서비스별로 "00" 또는 "0"을 성공 코드로 내려줄 수 있어 둘 다 허용한다.
    private boolean isSuccess(Map<String, Object> response) {
        String resultCode = stringValue(header(response).get("resultCode"));
        return "00".equals(resultCode) || "0".equals(resultCode);
    }

    private Map<String, Object> header(Map<String, Object> response) {
        return mapValue(mapValue(response.get("response")).get("header"));
    }

    // KMA 응답 구조(response.body.items.item)를 안전하게 List<Map> 형태로 정규화한다.
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

    private record BaseDateTime(String date, String time) {
    }

    public record UltraSrtNcstData(Double temperature, Double precipitation, Integer humidity, Double windSpeed) {
        public static UltraSrtNcstData empty() {
            return new UltraSrtNcstData(null, null, null, null);
        }
    }

    public record VilageFcstData(String cloudCover, Double precipitation, Integer humidity, Double windSpeed, Double diurnalRange) {
        public static VilageFcstData empty() {
            return new VilageFcstData(null, null, null, null, null);
        }
    }
}
