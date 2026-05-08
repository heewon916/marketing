package com.matketing.be.domain.user.dto;

public record SyncInstagramResponse(
    boolean success,
    String message,
    InstagramData data
) {
    public record InstagramData(String instagramUserId, String instagramUsername, String profileImageUrl) {}
}
