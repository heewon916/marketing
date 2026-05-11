package com.matketing.be.domain.content.util;

import static org.assertj.core.api.Assertions.assertThat;

import com.matketing.be.domain.content.client.AirKoreaAirQualityClient;
import org.junit.jupiter.api.Test;

class WeatherUtilTest {

    @Test
    void convertsLongitudeLatitudeToKmaGrid() {
        KmaGridConverter.Grid grid = KmaGridConverter.convert(126.9780, 37.5665);

        assertThat(grid.nx()).isEqualTo(59);
        assertThat(grid.ny()).isEqualTo(126);
    }

    @Test
    void parsesPrecipitationValues() {
        assertThat(WeatherValueParser.parsePrecipitation("강수없음")).isEqualTo(0.0);
        assertThat(WeatherValueParser.parsePrecipitation("1mm 미만")).isEqualTo(0.5);
        assertThat(WeatherValueParser.parsePrecipitation("3.0mm")).isEqualTo(3.0);
        assertThat(WeatherValueParser.parsePrecipitation("30.0~50.0mm")).isEqualTo(30.0);
        assertThat(WeatherValueParser.parsePrecipitation("알수없음")).isNull();
    }

    @Test
    void calculatesDiscomfortIndex() {
        assertThat(DiscomfortIndexCalculator.calculate(18.5, 45)).isEqualTo(63);
        assertThat(DiscomfortIndexCalculator.calculate(null, 45)).isNull();
    }

    @Test
    void convertsSkyCode() {
        assertThat(WeatherValueParser.convertSky("1")).isEqualTo("맑음");
        assertThat(WeatherValueParser.convertSky("3")).isEqualTo("구름많음");
        assertThat(WeatherValueParser.convertSky("4")).isEqualTo("흐림");
        assertThat(WeatherValueParser.convertSky("2")).isNull();
    }

    @Test
    void filtersInvalidAirQualityValues() {
        assertThat(AirKoreaAirQualityClient.isValidAirValue("85", null)).isTrue();
        assertThat(AirKoreaAirQualityClient.isValidAirValue("-", null)).isFalse();
        assertThat(AirKoreaAirQualityClient.isValidAirValue("", null)).isFalse();
        assertThat(AirKoreaAirQualityClient.isValidAirValue("35", "장비점검")).isFalse();
        assertThat(AirKoreaAirQualityClient.isValidAirValue("35", "통신장애")).isFalse();
    }
}
