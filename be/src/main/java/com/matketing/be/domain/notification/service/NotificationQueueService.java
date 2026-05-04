package com.matketing.be.domain.notification.service;

import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationQueueService {

    private static final String QUEUE_KEY = "notification:dispatch:queue";
    private final StringRedisTemplate stringRedisTemplate;

    // 알림 ID를 Redis Queue에 적재한다.
    public void enqueue(UUID notificationId) {
        try {
            Long result = stringRedisTemplate.opsForList().rightPush(QUEUE_KEY, notificationId.toString());
            if (result == null) {
                throw new RuntimeException("Redis rightPush returned null");
            }
        } catch (Exception e) {
            log.error("Failed to enqueue notification id: {}", notificationId, e);
            throw new BusinessException(ErrorCode.NOTIFICATION_QUEUE_ENQUEUE_FAILED, e);
        }
    }

    // Redis Queue에서 알림 ID를 꺼내온다.
    public Optional<UUID> dequeue() {
        try {
            String value = stringRedisTemplate.opsForList().leftPop(QUEUE_KEY);
            if (value != null && !value.isBlank()) {
                return Optional.of(UUID.fromString(value));
            }
        } catch (Exception e) {
            log.error("Failed to dequeue notification", e);
        }
        return Optional.empty();
    }
}
