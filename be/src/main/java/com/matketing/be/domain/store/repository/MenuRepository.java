package com.matketing.be.domain.store.repository;

import com.matketing.be.domain.store.entity.Menu;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface MenuRepository extends JpaRepository<Menu, UUID> {
}
