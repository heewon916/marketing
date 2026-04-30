package com.matketing.be.domain.user.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "users")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "instagram_user_id", nullable = false, length = 100, unique = true)
    private String instagramUserId;

    @Column(name = "instagram_username", length = 100)
    private String instagramUsername;

    @Column(name = "access_token", columnDefinition = "TEXT")
    private String accessToken;

    @Column(name = "token_expires_at")
    private OffsetDateTime tokenExpiresAt;

    @Column(name = "camera_mic_granted")
    private Boolean cameraMicGranted;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;

    @Builder
    public User(String instagramUserId, String instagramUsername, String accessToken, OffsetDateTime tokenExpiresAt, Boolean cameraMicGranted) {
        this.instagramUserId = instagramUserId;
        this.instagramUsername = instagramUsername;
        this.accessToken = accessToken;
        this.tokenExpiresAt = tokenExpiresAt;
        this.cameraMicGranted = cameraMicGranted;
    }

    public User update(String instagramUsername, String accessToken, OffsetDateTime tokenExpiresAt) {
        this.instagramUsername = instagramUsername;
        this.accessToken = accessToken;
        this.tokenExpiresAt = tokenExpiresAt;
        return this;
    }
}
