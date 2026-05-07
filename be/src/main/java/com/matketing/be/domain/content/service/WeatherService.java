package com.matketing.be.domain.content.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.matketing.be.domain.content.client.AirKoreaAirQualityClient;
import com.matketing.be.domain.content.client.AirKoreaAirQualityClient.AirQualityData;
import com.matketing.be.domain.content.client.AirKoreaStationClient;
import com.matketing.be.domain.content.client.AirKoreaStationClient.Station;
import com.matketing.be.domain.content.client.KmaForecastClient;
import com.matketing.be.domain.content.client.KmaForecastClient.UltraSrtNcstData;
import com.matketing.be.domain.content.client.KmaForecastClient.VilageFcstData;
import com.matketing.be.domain.content.client.KmaWarningClient;
import com.matketing.be.domain.content.client.KmaWarningClient.WarningData;
import com.matketing.be.domain.content.config.WeatherProperties;
import com.matketing.be.domain.content.dto.AiWeatherRequest;
import com.matketing.be.domain.content.util.DiscomfortIndexCalculator;
import com.matketing.be.domain.content.util.KmaGridConverter;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class WeatherService implements WeatherContextProvider {

    private static final DateTimeFormatter CACHE_HOUR_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMddHH");
    private static final TypeReference<List<Station>> STATION_LIST_TYPE = new TypeReference<>() {
    };

    private final KmaForecastClient kmaForecastClient;
    private final KmaWarningClient kmaWarningClient;
    private final AirKoreaStationClient airKoreaStationClient;
    private final AirKoreaAirQualityClient airKoreaAirQualityClient;
    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final WeatherProperties properties;

    /**
     * [날씨 참고정보 조회]
     * - store 좌표가 없으면 게시글 생성에 필요한 위치 기준이 없으므로 400 도메인 예외를 발생시킨다.
     * - weather-context:{storeId}:{yyyyMMddHH} 키로 같은 시간대 결과를 Redis에서 먼저 조회한다.
     * - 캐시가 없거나 깨져 있으면 외부 API를 호출해 새 컨텍스트를 만든 뒤 TTL과 함께 저장한다.
     * @param store 매장 주소/위도/경도/ID 정보
     * @param now 조회 기준 시각
     * @return AI 서버 요청 body에 들어갈 weather JSON
     */
    @Override
    public AiWeatherRequest getWeatherContext(Store store, LocalDateTime now) {
        validateCoordinates(store);

        String cacheKey = weatherContextKey(store.getId().toString(), now);
        String cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null && !cached.isBlank()) {
            try {
                return objectMapper.readValue(cached, AiWeatherRequest.class);
            } catch (JsonProcessingException exception) {
                log.warn("weather.cache.invalid: key={}", cacheKey, exception);
            }
        }

        AiWeatherRequest weather = fetchWeatherContext(store, now);
        try {
            redisTemplate.opsForValue().set(
                    cacheKey,
                    objectMapper.writeValueAsString(weather),
                    Duration.ofSeconds(properties.cacheTtlSeconds())
            );
        } catch (JsonProcessingException exception) {
            log.warn("weather.cache.write-failed: key={}", cacheKey, exception);
        }
        return weather;
    }

    /**
     * [외부 API 기반 날씨 컨텍스트 생성]
     * - 매장 위경도를 기상청 nx/ny 격자로 변환한다.
     * - 초단기실황, 단기예보, 특보, 에어코리아 대기질을 각각 조회한다.
     * - 초단기실황 값을 우선 사용하고, 없는 값은 단기예보 값으로 보완한다.
     * - 불쾌지수처럼 API에 없는 값은 직접 계산한다.
     * @param store 매장 정보
     * @param now 조회 기준 시각
     * @return 통합 weather DTO
     */
    private AiWeatherRequest fetchWeatherContext(Store store, LocalDateTime now) {
        double latitude = store.getLatitude().doubleValue();
        double longitude = store.getLongitude().doubleValue();
        KmaGridConverter.Grid grid = KmaGridConverter.convert(longitude, latitude);

        UltraSrtNcstData ultra = kmaForecastClient.getUltraSrtNcst(now, grid.nx(), grid.ny());
        VilageFcstData vilage = kmaForecastClient.getVilageFcst(now, grid.nx(), grid.ny());
        WarningData warning = getCachedWarnings(store.getAddress());
        AirQualityData airQuality = getAirQuality(store.getAddress(), longitude, latitude);

        Double temperature = firstNonNull(ultra.temperature(), null);
        Double precipitation = firstNonNull(ultra.precipitation(), vilage.precipitation());
        Integer humidity = firstNonNull(ultra.humidity(), vilage.humidity());
        Double windSpeed = firstNonNull(ultra.windSpeed(), vilage.windSpeed());
        Integer discomfortIndex = DiscomfortIndexCalculator.calculate(temperature, humidity);

        return new AiWeatherRequest(
                temperature,
                precipitation,
                vilage.cloudCover(),
                humidity,
                windSpeed,
                airQuality.pm10(),
                airQuality.pm25(),
                vilage.diurnalRange(),
                discomfortIndex,
                warning.heavyRainWarning(),
                warning.typhoonWarning()
        );
    }

    /**
     * [기상특보 캐시 조회]
     * - 특보는 짧게 변할 수 있어 별도 TTL을 사용한다.
     * - 주소에서 추출한 시도 기준으로 캐시하되, 실제 지역 매칭은 KmaWarningClient에서 한 번 더 처리한다.
     * @param address 매장 주소
     * @return 호우/태풍 특보 값
     */
    private WarningData getCachedWarnings(String address) {
        String sido = AirKoreaStationClient.extractSido(address);
        String cacheKey = "weather-warning:" + (sido == null ? "unknown" : sido);
        String cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null && !cached.isBlank()) {
            try {
                return objectMapper.readValue(cached, WarningData.class);
            } catch (JsonProcessingException exception) {
                log.warn("weather.warning-cache.invalid: key={}", cacheKey, exception);
            }
        }

        WarningData warning = kmaWarningClient.getWarnings(address);
        try {
            redisTemplate.opsForValue().set(
                    cacheKey,
                    objectMapper.writeValueAsString(warning),
                    Duration.ofSeconds(properties.warningCacheTtlSeconds())
            );
        } catch (JsonProcessingException exception) {
            log.warn("weather.warning-cache.write-failed: key={}", cacheKey, exception);
        }
        return warning;
    }

    /**
     * [대기질 조회]
     * - 매장 주소에서 시도명을 추출해 해당 지역 측정소 목록을 가져온다.
     * - 매장 위경도와 측정소 좌표의 Haversine 거리로 가장 가까운 측정소를 고른다.
     * - 선택한 측정소명으로 PM10/PM2.5 최신 유효값을 조회한다.
     * @param address 매장 주소
     * @param longitude 매장 경도
     * @param latitude 매장 위도
     * @return PM10/PM2.5 값
     */
    private AirQualityData getAirQuality(String address, double longitude, double latitude) {
        String sido = AirKoreaStationClient.extractSido(address);
        if (sido == null || sido.isBlank()) {
            log.warn("weather.airkorea.station-region-unmatched: address={}", address);
            return AirQualityData.empty();
        }

        List<Station> stations = getCachedStations(sido);
        Station nearestStation = airKoreaStationClient.nearestStation(stations, longitude, latitude);
        if (nearestStation == null) {
            log.warn("weather.airkorea.station-not-found: sido={}", sido);
            return AirQualityData.empty();
        }
        return airKoreaAirQualityClient.getAirQuality(nearestStation.stationName());
    }

    /**
     * [에어코리아 측정소 목록 캐시]
     * - 측정소 목록은 자주 바뀌지 않으므로 시도 단위로 장기 캐시한다.
     * - 캐시 파싱 실패 시 외부 API를 다시 호출해 복구한다.
     * @param sido 시도명
     * @return 측정소 목록
     */
    private List<Station> getCachedStations(String sido) {
        String cacheKey = "airkorea-stations:" + sido;
        String cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null && !cached.isBlank()) {
            try {
                return objectMapper.readValue(cached, STATION_LIST_TYPE);
            } catch (JsonProcessingException exception) {
                log.warn("weather.station-cache.invalid: key={}", cacheKey, exception);
            }
        }

        List<Station> stations = airKoreaStationClient.getStations(sido);
        try {
            redisTemplate.opsForValue().set(
                    cacheKey,
                    objectMapper.writeValueAsString(stations),
                    Duration.ofSeconds(properties.stationCacheTtlSeconds())
            );
        } catch (JsonProcessingException exception) {
            log.warn("weather.station-cache.write-failed: key={}", cacheKey, exception);
        }
        return stations;
    }

    // 매장 좌표가 없으면 기상청 격자 변환과 측정소 거리 계산을 할 수 없으므로 즉시 실패 처리한다.
    private void validateCoordinates(Store store) {
        if (store.getLatitude() == null || store.getLongitude() == null) {
            throw new BusinessException(ErrorCode.STORE_COORDINATE_REQUIRED);
        }
    }

    // 같은 매장/같은 시간대의 반복 호출을 묶기 위한 weather context 캐시 키다.
    private String weatherContextKey(String storeId, LocalDateTime now) {
        return "weather-context:" + storeId + ":" + now.format(CACHE_HOUR_FORMATTER);
    }

    // 실황 API 값을 우선 사용하고, 없을 때 예보 API fallback 값을 사용한다.
    private <T> T firstNonNull(T first, T second) {
        return first != null ? first : second;
    }
}
