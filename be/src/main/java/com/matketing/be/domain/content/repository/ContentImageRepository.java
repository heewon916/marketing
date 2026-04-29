package com.matketing.be.domain.content.repository;

import com.matketing.be.domain.content.entity.ContentImage;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ContentImageRepository extends JpaRepository<ContentImage, UUID> {

    // 이미지가 특정 게시물에 속하는지 함께 검증한다.
    Optional<ContentImage> findByIdAndContent_Id(UUID id, Long contentId);

    long countByContent_Id(Long contentId);
}
