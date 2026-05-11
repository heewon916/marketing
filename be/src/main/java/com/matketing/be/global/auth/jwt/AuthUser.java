package com.matketing.be.global.auth.jwt;

import com.matketing.be.domain.user.entity.User;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.Collections;
import java.util.UUID;

@Getter
@RequiredArgsConstructor
public class AuthUser implements UserDetails {

    private final UUID id;
    private final String instagramUserId;
    private final String instagramUsername;
    private final String profileImageUrl;

    public static AuthUser from(User user) {
        return new AuthUser(
                user.getId(),
                user.getInstagramUserId(),
                user.getInstagramUsername(),
                user.getProfileImageUrl()
        );
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER"));
    }

    @Override
    public String getPassword() {
        return "";
    }

    @Override
    public String getUsername() {
        return instagramUserId;
    }

    public String getProfileImageUrl() { return profileImageUrl; }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return true;
    }
}
