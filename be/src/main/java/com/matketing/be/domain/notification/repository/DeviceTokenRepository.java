package com.matketing.be.domain.notification.repository;

import com.matketing.be.domain.notification.entity.DeviceToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface DeviceTokenRepository extends JpaRepository<DeviceToken, UUID> {
    Optional<DeviceToken> findByToken(String token);
    List<DeviceToken> findByUserIdAndIsActiveTrue(UUID userId);
    List<DeviceToken> findByUserId(UUID userId);
}
