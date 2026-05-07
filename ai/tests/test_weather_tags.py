from datetime import date

import pytest

from app.schemas.sessions import WeatherInfo
from app.services.weather_tags import (
    HUMID_HIGH,
    HUMID_LOW,
    PRECIP_CLEAR,
    PRECIP_CLOUDY,
    PRECIP_HEAVY_RAIN,
    PRECIP_RAIN,
    SPECIAL_FINE_DUST,
    SPECIAL_SEASONAL_CHANGE,
    SPECIAL_TYPHOON,
    TEMP_COLD,
    TEMP_FREEZING,
    TEMP_HOT,
    TEMP_MILD,
    TEMP_SCORCHING,
    evaluate_weather_tags,
)


def make_weather(**overrides: float | str | None) -> WeatherInfo:
    payload = {
        "temperature": 18.5,
        "precipitation": 0.0,
        "cloud_cover": "맑음",
        "humidity": 45.0,
        "wind_speed": 2.5,
        "pm10": 20.0,
        "pm25": 10.0,
        "diurnal_range": 8.0,
        "discomfort_index": 63.0,
        "heavy_rain_warning": None,
        "typhoon_warning": None,
    }
    payload.update(overrides)
    return WeatherInfo(**payload)


@pytest.mark.parametrize(
    ("cloud_cover", "expected_tag"),
    [
        ("맑음", PRECIP_CLEAR),
        ("clear", PRECIP_CLEAR),
        ("흐림", PRECIP_CLOUDY),
        ("cloudy", PRECIP_CLOUDY),
        ("구름많음", PRECIP_CLOUDY),
    ],
)
def test_evaluate_weather_tags_maps_cloud_cover_strings(
    cloud_cover: str,
    expected_tag: str,
) -> None:
    weather = make_weather(cloud_cover=cloud_cover)

    tags = evaluate_weather_tags(weather, target_date=date(2026, 4, 27))

    assert tags[0] == expected_tag


@pytest.mark.parametrize(
    ("temperature", "expected_tag"),
    [
        (0.0, TEMP_FREEZING),
        (12.0, TEMP_COLD),
        (23.0, TEMP_MILD),
        (30.0, TEMP_HOT),
        (30.1, TEMP_SCORCHING),
    ],
)
def test_evaluate_weather_tags_assigns_temperature_bands(
    temperature: float,
    expected_tag: str,
) -> None:
    weather = make_weather(temperature=temperature)

    tags = evaluate_weather_tags(weather, target_date=date(2026, 4, 27))

    assert expected_tag in tags


def test_evaluate_weather_tags_distinguishes_rain_and_heavy_rain() -> None:
    rainy = make_weather(precipitation=2.0, cloud_cover="흐림")
    heavy = make_weather(precipitation=12.0, cloud_cover="흐림")
    warned = make_weather(
        precipitation=1.0,
        cloud_cover="흐림",
        heavy_rain_warning="호우주의보",
    )

    rainy_tags = evaluate_weather_tags(rainy, target_date=date(2026, 4, 27))
    heavy_tags = evaluate_weather_tags(heavy, target_date=date(2026, 4, 27))
    warned_tags = evaluate_weather_tags(warned, target_date=date(2026, 4, 27))

    assert rainy_tags[0] == PRECIP_RAIN
    assert PRECIP_HEAVY_RAIN not in rainy_tags
    assert heavy_tags[0] == PRECIP_HEAVY_RAIN
    assert warned_tags[0] == PRECIP_HEAVY_RAIN


def test_evaluate_weather_tags_adds_humidity_and_special_tags() -> None:
    weather = make_weather(
        humidity=75.0,
        discomfort_index=76.0,
        pm10=90.0,
        wind_speed=18.0,
        diurnal_range=11.0,
    )

    tags = evaluate_weather_tags(weather, target_date=date(2026, 4, 27))

    assert HUMID_HIGH in tags
    assert SPECIAL_FINE_DUST in tags
    assert SPECIAL_TYPHOON in tags
    assert SPECIAL_SEASONAL_CHANGE in tags


def test_evaluate_weather_tags_adds_humid_low_and_october_seasonal_change() -> None:
    weather = make_weather(humidity=40.0, diurnal_range=5.0)

    tags = evaluate_weather_tags(weather, target_date=date(2026, 10, 7))

    assert HUMID_LOW in tags
    assert SPECIAL_SEASONAL_CHANGE in tags


def test_evaluate_weather_tags_returns_stable_order_without_duplicates() -> None:
    weather = make_weather(
        temperature=18.5,
        precipitation=0.0,
        cloud_cover="맑음",
        humidity=45.0,
        pm10=85.0,
        pm25=35.0,
        diurnal_range=12.0,
    )

    tags = evaluate_weather_tags(weather, target_date=date(2026, 4, 27))

    assert tags == [
        PRECIP_CLEAR,
        TEMP_MILD,
        SPECIAL_FINE_DUST,
        SPECIAL_SEASONAL_CHANGE,
    ]
