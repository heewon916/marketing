package com.matketing.be.domain.content.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiWeatherRequest(
        Double temperature,
        Double precipitation,
        @JsonProperty("cloud_cover")
        String cloudCover,
        Integer humidity,
        @JsonProperty("wind_speed")
        Double windSpeed,
        Integer pm10,
        Integer pm25,
        @JsonProperty("diurnal_range")
        Double diurnalRange,
        @JsonProperty("discomfort_index")
        Double discomfortIndex,
        @JsonProperty("heavy_rain_warning")
        String heavyRainWarning,
        @JsonProperty("typhoon_warning")
        String typhoonWarning
) {

    public static AiWeatherRequest empty() {
        return new AiWeatherRequest(null, null, null, null, null, null, null, null, null, null, null);
    }
}
