package com.matketing.be.domain.content.repository;

import com.matketing.be.domain.content.entity.ContentImage;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ContentImageRepository extends JpaRepository<ContentImage, UUID> {

    Optional<ContentImage> findByContent_SessionIdAndS3Key(UUID sessionId, String s3Key);

    long countByContent_SessionId(UUID sessionId);
}
