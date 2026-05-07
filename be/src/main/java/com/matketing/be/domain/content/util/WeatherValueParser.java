package com.matketing.be.domain.content.util;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class WeatherValueParser {

    private static final Pattern NUMBER_PATTERN = Pattern.compile("-?\\d+(?:\\.\\d+)?");

    private WeatherValueParser() {
    }

    public static Double parseDouble(String value) {
        if (value == null || value.isBlank() || "-".equals(value.trim())) {
            return null;
        }
        try {
            return Double.parseDouble(value.trim());
        } catch (NumberFormatException exception) {
            return null;
        }
    }

    public static Integer parseInteger(String value) {
        Double parsed = parseDouble(value);
        return parsed == null ? null : (int) Math.round(parsed);
    }

    public static Double parsePrecipitation(String value) {
        if (value == null || value.isBlank() || "-".equals(value.trim())) {
            return null;
        }
        String normalized = value.trim();
        if ("강수없음".equals(normalized) || "0".equals(normalized)) {
            return 0.0;
        }
        if (normalized.contains("1mm 미만")) {
            return 0.5;
        }
        Matcher matcher = NUMBER_PATTERN.matcher(normalized.replace(",", ""));
        if (matcher.find()) {
            return parseDouble(matcher.group());
        }
        return null;
    }

    public static String convertSky(String code) {
        return switch (code) {
            case "1" -> "맑음";
            case "3" -> "구름많음";
            case "4" -> "흐림";
            default -> null;
        };
    }
}
