package com.matketing.be.global.auth.jwt;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.matketing.be.domain.user.entity.User;
import com.matketing.be.domain.user.repository.UserRepository;
import com.matketing.be.global.exception.ErrorCode;
import com.matketing.be.global.exception.ErrorResponse;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Optional;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider jwtTokenProvider;
    private final ObjectMapper objectMapper;
    private final UserRepository userRepository;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        String requestURI = request.getRequestURI();
        log.info("[JWT Filter] Request URI: {}", requestURI);

        String bearerToken = request.getHeader("Authorization");
        log.info("[JWT Filter] Authorization header exists: {}", StringUtils.hasText(bearerToken));

        if (StringUtils.hasText(bearerToken)) {
            boolean startsWithBearer = bearerToken.startsWith("Bearer ");
            log.info("[JWT Filter] Authorization header starts with 'Bearer ': {}", startsWithBearer);

            if (startsWithBearer) {
                String token = bearerToken.substring(7);
                log.info("[JWT Filter] tokenLength: {}", token.length());

                boolean isValid = jwtTokenProvider.validateToken(token);

                if (isValid) {
                    try {
                        String subject = jwtTokenProvider.getUsernameFromToken(token);
                        log.info("[JWT Filter] validateToken result: true, subject: {}, expiration: {}", subject, jwtTokenProvider.getExpirationDateFromToken(token));

                        if (StringUtils.hasText(subject)) {
                            Optional<User> optionalUser = userRepository.findByInstagramUserId(subject);
                            log.info("[JWT Filter] User lookup result: {}", optionalUser.isPresent());

                            if (optionalUser.isPresent()) {
                                AuthUser authUser = AuthUser.from(optionalUser.get());

                                UsernamePasswordAuthenticationToken authentication =
                                        new UsernamePasswordAuthenticationToken(authUser, null, authUser.getAuthorities());
                                
                                SecurityContextHolder.getContext().setAuthentication(authentication);
                            } else {
                                log.warn("[JWT Filter] User not found in DB. Skipping authentication.");
                                sendUnauthorizedError(response);
                                return;
                            }
                        } else {
                            log.warn("[JWT Filter] Subject is empty, skipping authentication.");
                            sendUnauthorizedError(response);
                            return;
                        }
                    } catch (Exception e) {
                        log.error("[JWT Filter] Exception during authentication setup: {}", e.getMessage(), e);
                        sendUnauthorizedError(response);
                        return;
                    }
                } else {
                    log.warn("[JWT Filter] Token validation failed.");
                    sendUnauthorizedError(response);
                    return;
                }
            } else {
                log.warn("[JWT Filter] Authorization header does not start with Bearer.");
            }
        } else {
            log.info("[JWT Filter] No Authorization header found.");
        }

        filterChain.doFilter(request, response);
    }

    private void sendUnauthorizedError(HttpServletResponse response) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");
        ErrorResponse errorResponse = ErrorResponse.of(ErrorCode.UNAUTHORIZED_USER);
        response.getWriter().write(objectMapper.writeValueAsString(errorResponse));
    }
}
