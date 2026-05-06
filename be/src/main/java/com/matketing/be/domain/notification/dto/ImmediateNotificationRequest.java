package com.matketing.be.domain.notification.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.matketing.be.domain.notification.enums.NotificationType;
import jakarta.validation.constraints.NotNull;
import java.util.UUID;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class ImmediateNotificationRequest {
    
    @NotNull(message = "store_id is required")
    @JsonProperty("store_id")
    private UUID storeId;

    @NotNull(message = "type is required")
    @JsonProperty("type")
    private NotificationType type;

    @NotNull(message = "reference_id is required")
    @JsonProperty("reference_id")
    private UUID referenceId;
}
