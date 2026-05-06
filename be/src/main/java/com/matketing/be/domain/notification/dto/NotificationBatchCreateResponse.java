package com.matketing.be.domain.notification.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class NotificationBatchCreateResponse {
    
    @JsonProperty("created_count")
    private int createdCount;

    @JsonProperty("skipped_count")
    private int skippedCount;
}
