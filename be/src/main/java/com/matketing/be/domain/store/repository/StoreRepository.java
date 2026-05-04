package com.matketing.be.domain.store.repository;

import com.matketing.be.domain.store.entity.Store;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface StoreRepository extends JpaRepository<Store, UUID> {
}
