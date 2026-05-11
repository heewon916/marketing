package com.matketing.be.domain.content.service;

import com.matketing.be.domain.content.dto.AiWeatherRequest;
import com.matketing.be.domain.store.entity.Store;
import java.time.LocalDateTime;

public interface WeatherContextProvider {

    AiWeatherRequest getWeatherContext(Store store, LocalDateTime now);
}
