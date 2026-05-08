package com.matketing.be.global.auth.jwt;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
public class JwtTokenProvider {

    private final SecretKey key;
    private final long accessTokenValidityInMs;
    private final long refreshTokenValidityInMs;

    public JwtTokenProvider(
            @Value("${jwt.secret}") String secretKey,
            @Value("${jwt.access-token-validity-in-ms}") long accessTokenValidityInMs,
            @Value("${jwt.refresh-token-validity-in-ms}") long refreshTokenValidityInMs) {
        this.key = Keys.hmacShaKeyFor(secretKey.getBytes(StandardCharsets.UTF_8));
        this.accessTokenValidityInMs = accessTokenValidityInMs;
        this.refreshTokenValidityInMs = refreshTokenValidityInMs;
        log.info("JwtTokenProvider initialized with secretLength={}, accessValidityMs={}, refreshValidityMs={}", 
                secretKey.length(), accessTokenValidityInMs, refreshTokenValidityInMs);
    }

    public String createAccessToken(Authentication authentication) {
        return createAccessToken(authentication.getName());
    }

    public String createAccessToken(String subject) {
        Date now = new Date();
        Date validity = new Date(now.getTime() + accessTokenValidityInMs);

        return Jwts.builder()
                .subject(subject)
                .issuedAt(now)
                .expiration(validity)
                .signWith(key)
                .compact();
    }

    public String createRefreshToken(Authentication authentication) {
        Date now = new Date();
        Date validity = new Date(now.getTime() + refreshTokenValidityInMs);

        return Jwts.builder()
                .subject(authentication.getName())
                .issuedAt(now)
                .expiration(validity)
                .signWith(key)
                .compact();
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parser().verifyWith(key).build().parseSignedClaims(token);
            return true;
        } catch (io.jsonwebtoken.ExpiredJwtException e) {
            log.warn("JWT validation failed: 만료 토큰 (ExpiredJwtException) - message: {}", e.getMessage());
        } catch (io.jsonwebtoken.security.SignatureException e) {
            log.warn("JWT validation failed: JWT_SECRET 불일치 또는 서명 검증 실패 (SignatureException) - message: {}", e.getMessage());
        } catch (io.jsonwebtoken.MalformedJwtException e) {
            log.warn("JWT validation failed: 토큰 형식 오류 (MalformedJwtException) - message: {}", e.getMessage());
        } catch (io.jsonwebtoken.UnsupportedJwtException e) {
            log.warn("JWT validation failed: 지원하지 않는 토큰 (UnsupportedJwtException) - message: {}", e.getMessage());
        } catch (IllegalArgumentException e) {
            log.warn("JWT validation failed: 빈 토큰 또는 잘못된 인자 (IllegalArgumentException) - message: {}", e.getMessage());
        } catch (io.jsonwebtoken.JwtException e) {
            log.warn("JWT validation failed: 기타 JWT 예외 (JwtException) - message: {}", e.getMessage());
        } catch (Exception e) {
            log.error("JWT validation failed: 예상 못한 예외 (Exception) - message: {}", e.getMessage(), e);
        }
        return false;
    }

    public String getUsernameFromToken(String token) {
        return Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload().getSubject();
    }

    public Date getExpirationDateFromToken(String token) {
        return Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload().getExpiration();
    }
}
