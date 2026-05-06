package com.matketing.be.domain.notification.controller;

import com.matketing.be.domain.notification.dto.ImmediateNotificationRequest;
import com.matketing.be.domain.notification.dto.ImmediateNotificationResponse;
import com.matketing.be.domain.notification.service.ImmediateNotificationService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/internal/notifications")
@RequiredArgsConstructor
public class InternalImmediateNotificationController {

    private final ImmediateNotificationService immediateNotificationService;

    // 내부 이벤트 발생 시 즉시 알림을 생성하고 Redis Queue에 적재한다.
    // TODO: 추후 internal/admin 인증 필요
    @PostMapping("/send-immediate")
    public ResponseEntity<ImmediateNotificationResponse> sendImmediate(
            @Valid @RequestBody ImmediateNotificationRequest request) {
        
        ImmediateNotificationResponse response = immediateNotificationService.sendImmediate(
                request.getStoreId(),
                request.getType(),
                request.getReferenceId()
        );
        
        return ResponseEntity.ok(response);
    }
}
