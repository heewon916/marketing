package com.matketing.be.domain.user.dto;

public record SimpleApiResponse(
    boolean success,
    String message
) {}
