package com.matketing.be.domain.notification.repository;

import com.matketing.be.domain.notification.entity.Notification;
import com.matketing.be.domain.notification.enums.NotificationStatus;
import com.matketing.be.domain.notification.enums.NotificationType;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface NotificationRepository extends JpaRepository<Notification, UUID> {
    List<Notification> findByStatusAndScheduledAtLessThanEqualOrderByScheduledAtAsc(NotificationStatus status, OffsetDateTime scheduledAt, Pageable pageable);
    List<Notification> findByStatus(NotificationStatus status, Pageable pageable);
    List<Notification> findByType(NotificationType type, Pageable pageable);
    List<Notification> findByTypeAndStatus(NotificationType type, NotificationStatus status, Pageable pageable);
    List<Notification> findByStoreId(UUID storeId, Pageable pageable);
}
