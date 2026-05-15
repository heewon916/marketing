package com.matketing.be.global.exception;

import java.util.LinkedHashMap;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    // 서비스 계층에서 의도적으로 던진 도메인/비즈니스 예외는 ErrorCode에 정의된 상태 코드와 메시지를 그대로 응답한다.
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusinessException(BusinessException exception) {
        ErrorCode errorCode = exception.getErrorCode();
        return ResponseEntity
                .status(errorCode.getStatus())
                .body(ErrorResponse.of(errorCode));
    }

    // @Valid 검증 실패는 필드별 메시지를 모아 내려준다. 같은 필드에 여러 오류가 있으면 첫 번째 메시지만 사용한다.
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleMethodArgumentNotValidException(
            MethodArgumentNotValidException exception
    ) {
        Map<String, String> errors = new LinkedHashMap<>();
        exception.getBindingResult().getFieldErrors()
                .forEach(error -> errors.putIfAbsent(error.getField(), error.getDefaultMessage()));

        return ResponseEntity
                .status(ErrorCode.VALIDATION_ERROR.getStatus())
                .body(ErrorResponse.of(ErrorCode.VALIDATION_ERROR, errors));
    }

    // 컨트롤러/서비스에서 잘못된 요청 값을 IllegalArgumentException으로 표현한 경우 400 응답으로 처리한다.
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handleIllegalArgumentException(IllegalArgumentException exception) {
        log.warn("Illegal argument exception", exception);
        return ResponseEntity
                .status(ErrorCode.INVALID_REQUEST.getStatus())
                .body(ErrorResponse.of(ErrorCode.INVALID_REQUEST));
    }

    // 파일 업로드 용량 초과 예외 처리 (413 Payload Too Large)
    @ExceptionHandler(org.springframework.web.multipart.MaxUploadSizeExceededException.class)
    public ResponseEntity<ErrorResponse> handleMaxUploadSizeExceededException(org.springframework.web.multipart.MaxUploadSizeExceededException exception) {
        log.warn("Max upload size exceeded", exception);
        return ResponseEntity
                .status(ErrorCode.PAYLOAD_TOO_LARGE.getStatus())
                .body(ErrorResponse.of(ErrorCode.PAYLOAD_TOO_LARGE));
    }

    @ExceptionHandler(org.springframework.web.multipart.MultipartException.class)
    public ResponseEntity<ErrorResponse> handleMultipartException(org.springframework.web.multipart.MultipartException exception) {
        log.warn("Multipart exception", exception);
        return ResponseEntity
                .status(ErrorCode.INVALID_REQUEST.getStatus())
                .body(ErrorResponse.of(ErrorCode.INVALID_REQUEST));
    }

    @ExceptionHandler({
            org.springframework.web.bind.MissingServletRequestParameterException.class,
            org.springframework.web.multipart.support.MissingServletRequestPartException.class
    })
    public ResponseEntity<ErrorResponse> handleMissingParameterException(Exception exception) {
        log.warn("Missing parameter/part exception", exception);
        return ResponseEntity
                .status(ErrorCode.INVALID_REQUEST.getStatus())
                .body(ErrorResponse.of(ErrorCode.INVALID_REQUEST));
    }

    // 위 분기에 걸리지 않은 예외는 예상하지 못한 서버 오류로 보고, 상세 내용은 로그에만 남긴다.
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleException(Exception exception) {
        log.error("Unhandled exception", exception);
        return ResponseEntity
                .status(ErrorCode.INTERNAL_SERVER_ERROR.getStatus())
                .body(ErrorResponse.of(ErrorCode.INTERNAL_SERVER_ERROR));
    }
}
