package com.matketing.be.global.exception;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public enum ErrorCode {

    INVALID_REQUEST(HttpStatus.BAD_REQUEST, "잘못된 요청입니다."),
    VALIDATION_ERROR(HttpStatus.BAD_REQUEST, "요청 값이 올바르지 않습니다."),

    UNAUTHORIZED_USER(HttpStatus.UNAUTHORIZED, "인증이 필요합니다."),
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "사용자를 찾을 수 없습니다."),

    CONTENT_NOT_FOUND(HttpStatus.NOT_FOUND, "게시물을 찾을 수 없습니다."),
    CONTENT_IMAGE_NOT_FOUND(HttpStatus.NOT_FOUND, "해당 게시물에 속한 이미지를 찾을 수 없습니다."),

    STT_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "음성 인식에 실패했습니다. 다시 녹음해 주세요."),
    STT_PARSING_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "텍스트 파싱에 실패했습니다."),
    INVALID_AUDIO_FILE(HttpStatus.BAD_REQUEST, "지원하지 않는 음성 파일입니다."),
    EMPTY_UTTERANCE(HttpStatus.BAD_REQUEST, "캡션 생성을 위한 문장을 입력해 주세요."),
    AI_SERVER_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "캡션 생성에 실패했습니다. 잠시 후 다시 시도해 주세요."),

    NOTIFICATION_NOT_FOUND(HttpStatus.NOT_FOUND, "알림을 찾을 수 없습니다."),
    INVALID_NOTIFICATION_BATCH_SIZE(HttpStatus.BAD_REQUEST, "유효하지 않은 알림 배치 크기입니다."),
    INVALID_NOTIFICATION_BATCH_TYPE(HttpStatus.BAD_REQUEST, "배치 생성할 수 없는 알림 타입입니다."),
    INVALID_NOTIFICATION_PAGE_REQUEST(HttpStatus.BAD_REQUEST, "알림 조회 페이지 요청 값이 올바르지 않습니다."),
    NOTIFICATION_QUEUE_ENQUEUE_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "알림 큐 적재에 실패했습니다."),
    NOTIFICATION_DISPATCH_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "알림 디스패치에 실패했습니다."),
    INVALID_IMMEDIATE_NOTIFICATION_TYPE(HttpStatus.BAD_REQUEST, "즉시 발송할 수 없는 알림 타입입니다."),
    IMMEDIATE_NOTIFICATION_ENQUEUE_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "즉시 알림을 큐에 적재하지 못했습니다."),

    MISSING_REFRESH_TOKEN(HttpStatus.BAD_REQUEST, "리프레시 토큰이 필요합니다."),
    INVALID_REFRESH_TOKEN(HttpStatus.UNAUTHORIZED, "유효하지 않은 리프레시 토큰입니다."),
    REFRESH_TOKEN_NOT_FOUND(HttpStatus.UNAUTHORIZED, "리프레시 토큰을 찾을 수 없습니다."),
    REFRESH_TOKEN_MISMATCH(HttpStatus.UNAUTHORIZED, "리프레시 토큰이 일치하지 않습니다."),

    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "사용자를 찾을 수 없습니다."),

    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "서버 내부 오류가 발생했습니다.");

    private final HttpStatus status;
    private final String message;

    ErrorCode(HttpStatus status, String message) {
        this.status = status;
        this.message = message;
    }
}
