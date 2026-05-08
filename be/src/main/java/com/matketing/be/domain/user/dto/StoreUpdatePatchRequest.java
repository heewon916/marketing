package com.matketing.be.domain.user.dto;

import java.util.Map;

public record StoreUpdatePatchRequest(
    String category,
    String address,
    Map<String, Object> operatingHours
) {}
