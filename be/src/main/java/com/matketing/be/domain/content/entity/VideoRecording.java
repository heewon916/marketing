package com.matketing.be.domain.content.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.UuidGenerator;

@Getter
@Entity
@Table(name = "video_recordings")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class VideoRecording {

    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "contents_id", nullable = false)
    private Content content;

    @Column(name = "s3_key", nullable = false, length = 200)
    private String s3Key;

    private VideoRecording(Content content, String s3Key) {
        this.content = content;
        this.s3Key = s3Key;
    }

    public static VideoRecording of(Content content, String s3Key) {
        return new VideoRecording(content, s3Key);
    }
}
