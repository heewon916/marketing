package com.matketing.be.domain.notification.controller;

import com.matketing.be.domain.notification.dto.NotificationHistoryItemResponse;
import com.matketing.be.domain.notification.dto.NotificationHistoryResponse;
import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.domain.notification.enums.NotificationStatus;
import com.matketing.be.domain.notification.enums.NotificationType;
import com.matketing.be.domain.notification.service.NotificationQueryService;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/internal/notifications")
@RequiredArgsConstructor
public class InternalNotificationQueryController {

    private final NotificationQueryService notificationQueryService;

    // 백엔드 운영/디버깅을 위한 알림 발송 이력을 조회한다.
    // TODO: 추후 internal/admin 인증 필요
    @GetMapping
    public ResponseEntity<NotificationHistoryResponse> getNotificationHistory(
            @RequestParam(required = false) NotificationType type,
            @RequestParam(required = false) NotificationStatus status,
            @RequestParam(name = "store_id", required = false) UUID storeId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        
        if (page < 0 || size <= 0 || size > 100) {
            throw new BusinessException(ErrorCode.INVALID_NOTIFICATION_PAGE_REQUEST);
        }

        PageRequest pageRequest = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        
        Page<Notification> notificationPage = notificationQueryService.findNotifications(type, status, storeId, pageRequest);
        
        List<NotificationHistoryItemResponse> items = notificationPage.getContent().stream()
                .map(NotificationHistoryItemResponse::from)
                .toList();

        NotificationHistoryResponse response = new NotificationHistoryResponse(
                items,
                notificationPage.getTotalElements(),
                notificationPage.getNumber(),
                notificationPage.getSize()
        );

        return ResponseEntity.ok(response);
    }
}
