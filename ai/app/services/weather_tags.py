from __future__ import annotations

from datetime import date

from app.schemas.sessions import WeatherInfo

PRECIP_CLEAR = "PRECIP_CLEAR"
PRECIP_CLOUDY = "PRECIP_CLOUDY"
PRECIP_RAIN = "PRECIP_RAIN"
PRECIP_HEAVY_RAIN = "PRECIP_HEAVY_RAIN"

TEMP_FREEZING = "TEMP_FREEZING"
TEMP_COLD = "TEMP_COLD"
TEMP_MILD = "TEMP_MILD"
TEMP_HOT = "TEMP_HOT"
TEMP_SCORCHING = "TEMP_SCORCHING"

HUMID_LOW = "HUMID_LOW"
HUMID_HIGH = "HUMID_HIGH"

SPECIAL_FINE_DUST = "SPECIAL_FINE_DUST"
SPECIAL_TYPHOON = "SPECIAL_TYPHOON"
SPECIAL_SEASONAL_CHANGE = "SPECIAL_SEASONAL_CHANGE"

_CLEAR_CLOUD_COVER_VALUES = {
    "clear",
    "sunny",
    "맑음",
}
_CLOUDY_CLOUD_COVER_VALUES = {
    "cloudy",
    "overcast",
    "흐림",
    "구름많음",
    "구름 많음",
}


def _normalize_cloud_cover(value: str) -> str:
    return value.strip().lower()


def _has_heavy_rain(weather: WeatherInfo) -> bool:
    return weather.precipitation >= 10 or bool(weather.heavy_rain_warning)


def evaluate_weather_tags(
    weather: WeatherInfo,
    *,
    target_date: date,
) -> list[str]:
    normalized_cloud_cover = _normalize_cloud_cover(weather.cloud_cover)
    tags: list[str] = []

    if _has_heavy_rain(weather):
        tags.append(PRECIP_HEAVY_RAIN)
    elif weather.precipitation > 0:
        tags.append(PRECIP_RAIN)
    elif normalized_cloud_cover in _CLEAR_CLOUD_COVER_VALUES:
        tags.append(PRECIP_CLEAR)
    elif normalized_cloud_cover in _CLOUDY_CLOUD_COVER_VALUES:
        tags.append(PRECIP_CLOUDY)

    if weather.temperature <= 0:
        tags.append(TEMP_FREEZING)
    elif weather.temperature <= 12:
        tags.append(TEMP_COLD)
    elif weather.temperature <= 23:
        tags.append(TEMP_MILD)
    elif weather.temperature <= 30:
        tags.append(TEMP_HOT)
    else:
        tags.append(TEMP_SCORCHING)

    if weather.humidity <= 40:
        tags.append(HUMID_LOW)
    if weather.humidity >= 70 or weather.discomfort_index > 75:
        tags.append(HUMID_HIGH)

    if weather.pm10 >= 81 or weather.pm25 >= 36:
        tags.append(SPECIAL_FINE_DUST)
    if weather.wind_speed >= 17 or bool(weather.typhoon_warning):
        tags.append(SPECIAL_TYPHOON)
    if weather.diurnal_range >= 10 or target_date.month in {3, 10}:
        tags.append(SPECIAL_SEASONAL_CHANGE)

    return tags
