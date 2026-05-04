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

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class NotificationQueryService {

    private final NotificationRepository notificationRepository;

    public Notification getById(UUID notificationId) {
        return notificationRepository.findById(notificationId)
                .orElseThrow(() -> new IllegalArgumentException("Notification not found with id: " + notificationId));
    }

    public List<Notification> findDueNotifications(int batchSize) {
        return notificationRepository.findByStatusAndScheduledAtLessThanEqualOrderByScheduledAtAsc(
                NotificationStatus.PENDING,
                OffsetDateTime.now(),
                PageRequest.of(0, batchSize)
        );
    }

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
