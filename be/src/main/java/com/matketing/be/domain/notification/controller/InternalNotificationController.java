package com.matketing.be.domain.notification.controller;

import com.matketing.be.domain.notification.dto.DispatchResult;
import com.matketing.be.domain.notification.dto.ImmediateNotificationRequest;
import com.matketing.be.domain.notification.dto.ImmediateNotificationResponse;
import com.matketing.be.domain.notification.dto.NotificationDispatchRequest;
import com.matketing.be.domain.notification.dto.NotificationDispatchResponse;
import com.matketing.be.domain.notification.dto.NotificationHistoryItemResponse;
import com.matketing.be.domain.notification.dto.NotificationHistoryResponse;
import com.matketing.be.domain.notification.dto.TestNotificationSendRequest;
import com.matketing.be.domain.notification.dto.TestNotificationSendResponse;
import com.matketing.be.domain.notification.entity.DeviceToken;
import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.domain.notification.enums.NotificationStatus;
import com.matketing.be.domain.notification.enums.NotificationType;
import com.matketing.be.domain.notification.repository.DeviceTokenRepository;
import com.matketing.be.domain.notification.service.FcmPushService;
import com.matketing.be.domain.notification.service.ImmediateNotificationService;
import com.matketing.be.domain.notification.service.NotificationDispatchService;
import com.matketing.be.domain.notification.service.NotificationQueryService;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import jakarta.validation.Valid;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/internal/notifications")
@RequiredArgsConstructor
public class InternalNotificationController {

    private final ImmediateNotificationService immediateNotificationService;
    private final NotificationDispatchService notificationDispatchService;
    private final NotificationQueryService notificationQueryService;
    private final DeviceTokenRepository deviceTokenRepository;
    private final FcmPushService fcmPushService;

    // TODO: 추후 관리자/내부 서비스 인증을 거치도록 Security 설정 필요
    @PostMapping("/test-send")
    public ResponseEntity<TestNotificationSendResponse> sendTestNotification(
            @Valid @RequestBody TestNotificationSendRequest request) {
        
        List<DeviceToken> activeTokens = deviceTokenRepository.findByUserIdAndIsActiveTrue(request.getUserId());

        int[] result = fcmPushService.sendPushNotification(
                activeTokens,
                request.getTitle(),
                request.getBody(),
                request.getWebUrl()
        );

        TestNotificationSendResponse response = TestNotificationSendResponse.builder()
                .status("success")
                .sentCount(result[0])
                .failedCount(result[1])
                .sentAt(OffsetDateTime.now())
                .build();

        return ResponseEntity.ok(response);
    }

    // 발송 예정 시간이 지난 알림을 Redis Queue에 적재하도록 트리거한다.
    // TODO: 추후 internal/admin 인증 필요
    @PostMapping("/dispatch")
    public ResponseEntity<NotificationDispatchResponse> dispatchNotifications(
            @Valid @RequestBody NotificationDispatchRequest request) {
        
        DispatchResult result = notificationDispatchService.dispatchDueNotifications(request.getBatchSize());
        
        return ResponseEntity.ok(NotificationDispatchResponse.from(result));
    }

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
