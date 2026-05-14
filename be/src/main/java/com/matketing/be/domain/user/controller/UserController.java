package com.matketing.be.domain.user.controller;

import com.matketing.be.domain.user.dto.TokenResponse;
import com.matketing.be.domain.user.dto.SimpleApiResponse;
import com.matketing.be.domain.user.dto.StoreUpdatePatchRequest;
import com.matketing.be.domain.user.dto.SyncInstagramResponse;
import com.matketing.be.domain.user.dto.UserMeResponse;
import com.matketing.be.domain.user.entity.User;
import com.matketing.be.domain.user.repository.UserRepository;
import com.matketing.be.domain.user.service.AuthService;
import com.matketing.be.domain.user.service.UserService;
import com.matketing.be.global.auth.jwt.JwtTokenProvider;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private static final String REFRESH_TOKEN_COOKIE = "refreshToken";

    private final AuthService authService;
    private final UserService userService;
    private final JwtTokenProvider jwtTokenProvider;
    private final UserRepository userRepository;

    private User getAuthenticatedUser(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            String token = bearerToken.substring(7);
            if (jwtTokenProvider.validateToken(token)) {
                String instagramUserId = jwtTokenProvider.getUsernameFromToken(token);
                return userRepository.findByInstagramUserId(instagramUserId)
                        .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
            }
        }
        
        // 세션 방식 (oauth2Login) 폴백
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getPrincipal() instanceof OAuth2User oauth2User) {
            String instagramUserId = oauth2User.getName();
            if (oauth2User.getAttributes().containsKey("id")) {
                instagramUserId = oauth2User.getAttributes().get("id").toString();
            }
            return userRepository.findByInstagramUserId(instagramUserId)
                    .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
        }
        throw new IllegalArgumentException("Unauthorized");
    }

    @PostMapping("/token/refresh")
    public ResponseEntity<TokenResponse> refresh(HttpServletRequest request) {
        String refreshToken = null;
        if (request.getCookies() != null) {
            for (Cookie cookie : request.getCookies()) {
                if (REFRESH_TOKEN_COOKIE.equals(cookie.getName())) {
                    refreshToken = cookie.getValue();
                    break;
                }
            }
        }

        if (refreshToken == null) {
            throw new BusinessException(ErrorCode.MISSING_REFRESH_TOKEN);
        }

        TokenResponse tokenResponse = authService.reissue(refreshToken);
        return ResponseEntity.ok(tokenResponse);
    }

    @GetMapping("/me")
    public ResponseEntity<UserMeResponse> getMe(HttpServletRequest request) {
        User user = getAuthenticatedUser(request);
        return ResponseEntity.ok(userService.getMe(user));
    }

    @PatchMapping("/me")
    public ResponseEntity<SimpleApiResponse> patchStore(
            HttpServletRequest request,
            @RequestBody StoreUpdatePatchRequest patchRequest) {
        User user = getAuthenticatedUser(request);
        return ResponseEntity.ok(userService.updateStore(user, patchRequest));
    }

    @DeleteMapping("/me")
    public ResponseEntity<SimpleApiResponse> deleteMe(HttpServletRequest request, HttpServletResponse response) {
        User user = getAuthenticatedUser(request);
        SimpleApiResponse res = userService.deleteUser(user);
        
        // 로그아웃 처리와 동일하게 쿠키 삭제
        Cookie refreshTokenCookie = new Cookie(REFRESH_TOKEN_COOKIE, null);
        refreshTokenCookie.setMaxAge(0);
        refreshTokenCookie.setPath("/");
        response.addCookie(refreshTokenCookie);
        
        return ResponseEntity.ok(res);
    }

    @PostMapping("/me/instagram/sync")
    public ResponseEntity<SyncInstagramResponse> syncInstagram(HttpServletRequest request) {
        User user = getAuthenticatedUser(request);
        return ResponseEntity.ok(userService.syncInstagram(user));
    }

    @PostMapping("/logout")
    public ResponseEntity<SimpleApiResponse> logout(HttpServletRequest request, HttpServletResponse response) {
        User user = getAuthenticatedUser(request);
        authService.logout(user.getInstagramUserId());

        Cookie refreshTokenCookie = new Cookie(REFRESH_TOKEN_COOKIE, null);
        refreshTokenCookie.setMaxAge(0);
        refreshTokenCookie.setPath("/");
        response.addCookie(refreshTokenCookie);

        return ResponseEntity.ok(new SimpleApiResponse(true, "로그아웃 성공"));
    }
}
