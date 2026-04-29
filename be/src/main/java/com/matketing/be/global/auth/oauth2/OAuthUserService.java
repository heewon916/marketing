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

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);
        
        Map<String, Object> attributes = oAuth2User.getAttributes();
        
        String instagramUserId = attributes.get("id") != null ? attributes.get("id").toString() : null;
        String instagramUsername = attributes.get("username") != null ? attributes.get("username").toString() : "instagram_user";
        
        String accessToken = userRequest.getAccessToken().getTokenValue();
        OffsetDateTime tokenExpiresAt = userRequest.getAccessToken().getExpiresAt() != null ? 
                userRequest.getAccessToken().getExpiresAt().atOffset(ZoneOffset.UTC) : null;

        // DB 확인 후 신규 유저 등록 또는 기존 유저 업데이트
        User user = saveOrUpdate(instagramUserId, instagramUsername, accessToken, tokenExpiresAt);

        return new DefaultOAuth2User(
                Collections.singleton(new SimpleGrantedAuthority("ROLE_USER")),
                attributes,
                "id"
        );
    }

    private User saveOrUpdate(String instagramUserId, String instagramUsername, String accessToken, OffsetDateTime tokenExpiresAt) {
        User user = userRepository.findByInstagramUserId(instagramUserId)
                .map(entity -> entity.update(instagramUsername, accessToken, tokenExpiresAt)) // 기존 유저면 정보 업데이트
                .orElse(User.builder()
                        .instagramUserId(instagramUserId)
                        .instagramUsername(instagramUsername)
                        .accessToken(accessToken)
                        .tokenExpiresAt(tokenExpiresAt)
                        .cameraMicGranted(false)
                        .build()); // 신규 유저면 생성
        return userRepository.save(user);
    }
}


