package com.matketing.be.domain.onboarding.repository;

import com.matketing.be.domain.onboarding.entity.PosPin;
import org.springframework.data.repository.CrudRepository;

public interface PosPinRepository extends CrudRepository<PosPin, String> {
}
