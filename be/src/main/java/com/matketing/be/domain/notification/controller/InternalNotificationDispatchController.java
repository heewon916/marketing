package com.matketing.be.domain.notification.controller;

import com.matketing.be.domain.notification.dto.DispatchResult;
import com.matketing.be.domain.notification.dto.NotificationDispatchRequest;
import com.matketing.be.domain.notification.dto.NotificationDispatchResponse;
import com.matketing.be.domain.notification.service.NotificationDispatchService;
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
public class InternalNotificationDispatchController {

    private final NotificationDispatchService notificationDispatchService;

    // 발송 예정 시간이 지난 알림을 Redis Queue에 적재하도록 트리거한다.
    // TODO: 추후 internal/admin 인증 필요
    @PostMapping("/dispatch")
    public ResponseEntity<NotificationDispatchResponse> dispatchNotifications(
            @Valid @RequestBody NotificationDispatchRequest request) {
        
        DispatchResult result = notificationDispatchService.dispatchDueNotifications(request.getBatchSize());
        
        return ResponseEntity.ok(NotificationDispatchResponse.from(result));
    }
}
