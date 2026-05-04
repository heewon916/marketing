package com.matketing.be.domain.user.service;

import com.matketing.be.domain.user.entity.RefreshToken;
import com.matketing.be.domain.user.repository.RefreshTokenRepository;
import com.matketing.be.domain.user.dto.TokenResponse;
import com.matketing.be.global.auth.jwt.JwtTokenProvider;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final JwtTokenProvider jwtTokenProvider;
    private final RefreshTokenRepository refreshTokenRepository;

    @Transactional
    public TokenResponse reissue(String refreshToken) {
        if (!jwtTokenProvider.validateToken(refreshToken)) {
            throw new BusinessException(ErrorCode.INVALID_REFRESH_TOKEN);
        }

        String userId = jwtTokenProvider.getUsernameFromToken(refreshToken);

        RefreshToken savedRefreshToken = refreshTokenRepository.findById(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.REFRESH_TOKEN_NOT_FOUND));

        if (!savedRefreshToken.getRefreshToken().equals(refreshToken)) {
            throw new BusinessException(ErrorCode.REFRESH_TOKEN_MISMATCH);
        }

        String newAccessToken = jwtTokenProvider.createAccessToken(userId);
        // ISO 8601 포맷 (예: 2026-06-22T00:00:00Z) 으로 변환
        String tokenExpiresAt = jwtTokenProvider.getExpirationDateFromToken(newAccessToken).toInstant().toString();

        return new TokenResponse(newAccessToken, tokenExpiresAt);
    }
}
