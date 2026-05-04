package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.domain.notification.enums.NotificationStatus;
import com.matketing.be.domain.notification.enums.NotificationType;
import com.matketing.be.domain.notification.repository.NotificationRepository;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class NotificationQueryService {

    private final NotificationRepository notificationRepository;

    // ID로 알림을 단건 조회하며, 없으면 예외를 발생시킨다.
    public Notification getById(UUID notificationId) {
        return notificationRepository.findById(notificationId)
                .orElseThrow(() -> new BusinessException(ErrorCode.NOTIFICATION_NOT_FOUND));
    }

    // 발송 예정 시간이 지난 대기(PENDING) 상태의 알림 목록을 지정한 개수만큼 조회한다.
    public List<Notification> findDueNotifications(int batchSize) {
        return notificationRepository.findByStatusAndScheduledAtLessThanEqualOrderByScheduledAtAsc(
                NotificationStatus.PENDING,
                OffsetDateTime.now(),
                PageRequest.of(0, batchSize)
        );
    }

    // 조건(타입, 상태, 매장 ID)에 맞는 알림 목록을 페이징하여 조회한다.
    public List<Notification> findNotifications(NotificationType type, NotificationStatus status, UUID storeId, Pageable pageable) {
        // TODO: 동적 쿼리를 사용하여 개선 필요. 현재는 파라미터 유무에 따라 분기 처리.
        if (type != null && status != null) {
            return notificationRepository.findByTypeAndStatus(type, status, pageable);
        } else if (status != null) {
            return notificationRepository.findByStatus(status, pageable);
        } else if (type != null) {
            return notificationRepository.findByType(type, pageable);
        } else if (storeId != null) {
            return notificationRepository.findByStoreId(storeId, pageable);
        } else {
            return notificationRepository.findAll(pageable).getContent();
        }
    }
}
