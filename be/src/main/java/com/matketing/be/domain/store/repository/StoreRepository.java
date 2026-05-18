package com.matketing.be.domain.store.repository;

import com.matketing.be.domain.store.entity.Store;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.UUID;

public interface StoreRepository extends JpaRepository<Store, UUID> {

    @Query(value = "select * from stores where user_id = :userId limit 1", nativeQuery = true)
    Optional<Store> findFirstByUserId(@Param("userId") UUID userId);
}
