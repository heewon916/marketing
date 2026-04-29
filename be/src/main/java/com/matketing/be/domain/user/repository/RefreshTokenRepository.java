package com.matketing.be.domain.user.repository;

import org.springframework.data.repository.CrudRepository;
import com.matketing.be.domain.user.entity.RefreshToken;

public interface RefreshTokenRepository extends CrudRepository<RefreshToken, String> {
}
