package com.matketing.be.domain.store.repository;

import com.matketing.be.domain.store.entity.StoreHours;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface StoreHoursRepository extends JpaRepository<StoreHours, UUID> {
}
