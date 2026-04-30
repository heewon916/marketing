package com.matketing.be.domain.user.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import com.matketing.be.domain.user.entity.User;

import java.util.Optional;
import java.util.UUID;

public interface UserRepository extends JpaRepository<User, UUID> {
    Optional<User> findByInstagramUserId(String instagramUserId);
}
