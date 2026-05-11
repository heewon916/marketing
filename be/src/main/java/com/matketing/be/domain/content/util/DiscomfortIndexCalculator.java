package com.matketing.be.domain.content.util;

public final class DiscomfortIndexCalculator {

    private DiscomfortIndexCalculator() {
    }

    public static Integer calculate(Double temperature, Integer humidity) {
        if (temperature == null || humidity == null) {
            return null;
        }
        double value = 0.81 * temperature + 0.01 * humidity * (0.99 * temperature - 14.3) + 46.3;
        return (int) Math.round(value);
    }
}
