package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiWeatherRequest(
        Double temperature,             // 온도
        Double precipitation,           // 강수량
        @JsonProperty("cloud_cover")
        String cloudCover,              // 구름 양: "맑음", "구름 많음", "흐림"
        Integer humidity,               // 습도
        @JsonProperty("wind_speed")
        Double windSpeed,               // 풍속
        Integer pm10,                   // 미세먼지10
        Integer pm25,                   // 미세먼지2.5
        @JsonProperty("diurnal_range")
        Double diurnalRange,            // 일교차
        @JsonProperty("discomfort_index")
        Integer discomfortIndex,        // 불쾌 지수
        @JsonProperty("heavy_rain_warning")
        String heavyRainWarning,        // 호우 주의보
        @JsonProperty("typhoon_warning")
        String typhoonWarning           // 태풍 주의보
) {

    public static AiWeatherRequest empty() {
        return new AiWeatherRequest(null, null, null, null, null, null, null, null, null, null, null);
    }
}
