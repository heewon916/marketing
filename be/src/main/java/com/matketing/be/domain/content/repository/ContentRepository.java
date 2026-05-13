package com.matketing.be.domain.content.repository;

import com.matketing.be.domain.content.entity.Content;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ContentRepository extends JpaRepository<Content, Long> {

    // 상세 조회 시 연관 이미지를 함께 읽어 N+1을 피한다.
    @EntityGraph(attributePaths = {"images", "videoRecordings"})
    Optional<Content> findWithImagesAndVideoRecordingsById(Long id);

    @EntityGraph(attributePaths = {"images", "videoRecordings"})
    Optional<Content> findWithImagesAndVideoRecordingsBySessionId(UUID sessionId);

    @org.springframework.data.jpa.repository.Query("""
        select count(c)
        from Content c
        where c.storeId = :storeId
          and c.publishedAt is not null
          and c.publishedAt >= :startAt
          and c.publishedAt < :endAt
          and c.instagramMediaId is not null
          and (c.isDeleted = false or c.isDeleted is null)
    """)
    long countPublishedContentsByStoreAndPeriod(
        @org.springframework.data.repository.query.Param("storeId") UUID storeId,
        @org.springframework.data.repository.query.Param("startAt") java.time.OffsetDateTime startAt,
        @org.springframework.data.repository.query.Param("endAt") java.time.OffsetDateTime endAt
    );
}
