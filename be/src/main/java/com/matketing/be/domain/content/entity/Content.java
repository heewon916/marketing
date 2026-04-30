package com.matketing.be.domain.content.entity;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Entity
@Table(name = "contents")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Content {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "store_id", nullable = false)
    private UUID storeId;

    @Column(name = "session_id")
    private UUID sessionId;

    @Column(columnDefinition = "TEXT")
    private String caption;

    @Column(name = "instagram_media_id", length = 100)
    private String instagramMediaId;

    @Column(name = "instagram_permalink", columnDefinition = "TEXT")
    private String instagramPermalink;

    @Column(name = "published_at")
    private OffsetDateTime publishedAt;

    @Column(name = "is_deleted")
    private Boolean isDeleted;

    @Column(name = "deleted_at")
    private OffsetDateTime deletedAt;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @OneToMany(mappedBy = "content", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @OrderBy("id ASC")
    private final List<ContentImage> images = new ArrayList<>();

    @OneToMany(mappedBy = "content", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private final List<VideoRecording> videoRecordings = new ArrayList<>();

    @Builder
    private Content(
            UUID storeId,
            UUID sessionId,
            String caption,
            String instagramMediaId,
            String instagramPermalink,
            OffsetDateTime publishedAt,
            Boolean isDeleted,
            OffsetDateTime deletedAt,
            OffsetDateTime createdAt
    ) {
        this.storeId = storeId;
        this.sessionId = sessionId;
        this.caption = caption;
        this.instagramMediaId = instagramMediaId;
        this.instagramPermalink = instagramPermalink;
        this.publishedAt = publishedAt;
        this.isDeleted = isDeleted;
        this.deletedAt = deletedAt;
        this.createdAt = createdAt;
    }

    public void update(
            UUID sessionId,
            String caption,
            String instagramMediaId,
            String instagramPermalink,
            OffsetDateTime publishedAt
    ) {
        this.sessionId = sessionId;
        this.caption = caption;
        this.instagramMediaId = instagramMediaId;
        this.instagramPermalink = instagramPermalink;
        this.publishedAt = publishedAt;
    }

    // 현재 스키마에서는 텍스트 수정 API가 caption만 변경 가능하므로 별도 메서드로 분리한다.
    public void updateCaption(String caption) {
        this.caption = caption;
    }

    public void replaceImages(List<String> s3Keys) {
        this.images.clear();
        if (s3Keys == null) {
            return;
        }
        s3Keys.forEach(this::addImage);
    }

    public void replaceVideoRecordings(List<String> s3Keys) {
        this.videoRecordings.clear();
        if (s3Keys == null) {
            return;
        }
        s3Keys.forEach(this::addVideoRecording);
    }

    public void softDelete(OffsetDateTime deletedAt) {
        this.isDeleted = true;
        this.deletedAt = deletedAt;
    }

    public void restore() {
        this.isDeleted = false;
        this.deletedAt = null;
    }

    private void addImage(String s3Key) {
        this.images.add(ContentImage.of(this, s3Key));
    }

    private void addVideoRecording(String s3Key) {
        this.videoRecordings.add(VideoRecording.of(this, s3Key));
    }
}
