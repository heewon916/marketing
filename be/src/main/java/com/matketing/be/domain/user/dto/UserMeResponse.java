package com.matketing.be.domain.user.dto;

public record UserMeResponse(
    UserDto user,
    StoreDto store,
    boolean isOnboarded
) {
    public record UserDto(String id, String instagramUserId, String instagramUsername, String profileImageUrl) {}
    public record StoreDto(String id, String merchantId, String category, String address, Object operatingHours) {}
}
