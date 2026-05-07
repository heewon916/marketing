package com.matketing.be.domain.content.enums;

import java.util.Locale;

public enum ContentStatus {
    STARTED,
    COMPLETED,
    TEXT_GENERATED,
    FRAME_EXTRACTED,
    PHOTO_EDITED;

    // Redis/API 표준 상태는 대문자 스네이크 케이스지만, 외부 시스템에서 소문자나 하이픈 표기가 들어올 수 있다.
    // 이 메서드는 외부 상태 문자열을 내부 표준 enum으로 맞추는 단일 진입점이다.
    // null/blank는 아직 명확한 결과가 없는 처리 중 상태로 보고 STARTED로 해석한다.
    public static ContentStatus fromExternal(String value) {
        if (value == null || value.isBlank()) {
            return STARTED;
        }

        // 외부 시스템에서 들어올 수 있는 소문자/하이픈 상태를 Redis/API 표준인 대문자 스네이크 케이스로 맞춘다.
        String normalized = value.trim()
                .replace("-", "_")
                .toUpperCase(Locale.ROOT);
        return ContentStatus.valueOf(normalized);
    }

    // 중복 요청에서 기존 Redis 결과가 프론트에 반환 가능한 텍스트 생성 이후 상태인지 판단할 때 사용할 수 있는 helper다.
    // 현재 구현에서는 STARTED 응답도 허용하므로 직접 사용하지 않지만, 상태 조회 API가 추가되면 재사용할 수 있다.
    public boolean isTextGeneratedOrAfter() {
        return this == TEXT_GENERATED
                || this == FRAME_EXTRACTED
                || this == PHOTO_EDITED
                || this == COMPLETED;
    }
}
