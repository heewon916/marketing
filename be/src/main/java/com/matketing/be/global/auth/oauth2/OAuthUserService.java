package com.matketing.be.global.auth.oauth2;

import com.matketing.be.domain.user.entity.User;
import com.matketing.be.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.DefaultOAuth2User;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.Collections;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class OAuthUserService extends DefaultOAuth2UserService {

    private final UserRepository userRepository;
    private final InstagramApiClient instagramApiClient;

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);
        
        Map<String, Object> attributes = oAuth2User.getAttributes();
        
        String instagramUserId = attributes.get("id") != null ? attributes.get("id").toString() : null;
        String instagramUsername = attributes.get("username") != null ? attributes.get("username").toString() : "instagram_user";
        String profileImageUrl = null; // Graph API doesn't always return this by default without extra request
        
        String shortLivedToken = userRequest.getAccessToken().getTokenValue();
        java.time.Instant expiresAt = userRequest.getAccessToken().getExpiresAt();
        OffsetDateTime tokenExpiresAt = expiresAt != null ? expiresAt.atOffset(ZoneOffset.UTC) : null;

        // 장기 토큰 교환 요청
        Map<String, Object> tokenData = instagramApiClient.exchangeForLongLivedToken(shortLivedToken);
        String finalAccessToken = shortLivedToken; // 기본값은 단기 토큰으로 유지

        if (tokenData != null && tokenData.containsKey("access_token")) {
            finalAccessToken = (String) tokenData.get("access_token");
            Object expiresInObj = tokenData.get("expires_in");
            if (expiresInObj instanceof Number) {
                tokenExpiresAt = OffsetDateTime.now(ZoneOffset.UTC).plusSeconds(((Number) expiresInObj).longValue());
            }
        }

        // 초기 로그인 시 프로필 정보(특히 프로필 사진) 자동으로 가져오기
        try {
            Map<String, Object> profile = instagramApiClient.getUserProfile(finalAccessToken);
            if (profile != null) {
                if (profile.get("username") != null) {
                    instagramUsername = profile.get("username").toString();
                }
                if (profile.get("profile_picture_url") != null) {
                    profileImageUrl = profile.get("profile_picture_url").toString();
                }
            }
        } catch (Exception e) {
            // 프로필 정보를 가져오는데 실패하더라도 로그인 프로세스는 정상 진행되도록 예외 무시
        }

        // DB 확인 후 신규 유저 등록 또는 기존 유저 업데이트
        saveOrUpdate(instagramUserId, instagramUsername, profileImageUrl, finalAccessToken, tokenExpiresAt);

        return new DefaultOAuth2User(
                Collections.singleton(new SimpleGrantedAuthority("ROLE_USER")),
                attributes,
                "id"
        );
    }

    private User saveOrUpdate(String instagramUserId, String instagramUsername, String profileImageUrl, String accessToken, OffsetDateTime tokenExpiresAt) {
        User user = userRepository.findByInstagramUserId(instagramUserId)
                .map(entity -> {
                    entity.update(instagramUsername, accessToken, tokenExpiresAt);
                    entity.updateProfile(instagramUsername, profileImageUrl);
                    return entity;
                }) // 기존 유저면 정보 업데이트
                .orElse(User.builder()
                        .instagramUserId(instagramUserId)
                        .instagramUsername(instagramUsername)
                        .profileImageUrl(profileImageUrl)
                        .accessToken(accessToken)
                        .tokenExpiresAt(tokenExpiresAt)
                        .build()); // 신규 유저면 생성
        return userRepository.save(user);
    }
}


