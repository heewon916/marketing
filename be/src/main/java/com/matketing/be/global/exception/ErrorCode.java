package com.matketing.be.global.exception;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public enum ErrorCode {

    INVALID_REQUEST(HttpStatus.BAD_REQUEST, "잘못된 요청입니다."),
    VALIDATION_ERROR(HttpStatus.BAD_REQUEST, "요청 값이 올바르지 않습니다."),

    CONTENT_NOT_FOUND(HttpStatus.NOT_FOUND, "게시물을 찾을 수 없습니다."),
    CONTENT_IMAGE_NOT_FOUND(HttpStatus.NOT_FOUND, "해당 게시물에 속한 이미지를 찾을 수 없습니다."),

    NOTIFICATION_NOT_FOUND(HttpStatus.NOT_FOUND, "알림을 찾을 수 없습니다."),
    INVALID_NOTIFICATION_BATCH_SIZE(HttpStatus.BAD_REQUEST, "유효하지 않은 알림 배치 크기입니다."),
    NOTIFICATION_QUEUE_ENQUEUE_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "알림 큐 적재에 실패했습니다."),
    NOTIFICATION_DISPATCH_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "알림 디스패치에 실패했습니다."),

    MISSING_REFRESH_TOKEN(HttpStatus.BAD_REQUEST, "리프레시 토큰이 필요합니다."),
    INVALID_REFRESH_TOKEN(HttpStatus.UNAUTHORIZED, "유효하지 않은 리프레시 토큰입니다."),
    REFRESH_TOKEN_NOT_FOUND(HttpStatus.UNAUTHORIZED, "리프레시 토큰을 찾을 수 없습니다."),
    REFRESH_TOKEN_MISMATCH(HttpStatus.UNAUTHORIZED, "리프레시 토큰이 일치하지 않습니다."),

    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "서버 내부 오류가 발생했습니다.");

    private final HttpStatus status;
    private final String message;

    ErrorCode(HttpStatus status, String message) {
        this.status = status;
        this.message = message;
    }
}
