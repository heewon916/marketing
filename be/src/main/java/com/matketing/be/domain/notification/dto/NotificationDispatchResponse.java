package com.matketing.be.domain.notification.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class NotificationDispatchResponse {
    
    @JsonProperty("dispatched_count")
    private int dispatchedCount;

    @JsonProperty("failed_count")
    private int failedCount;
    
    public static NotificationDispatchResponse from(DispatchResult result) {
        return new NotificationDispatchResponse(
            result.getDispatchedCount(),
            result.getFailedCount()
        );
    }
}
