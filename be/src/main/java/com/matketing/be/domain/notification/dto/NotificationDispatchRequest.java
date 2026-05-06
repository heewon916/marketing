package com.matketing.be.domain.notification.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class NotificationDispatchRequest {
    
    @NotNull(message = "batch_size is required")
    @Min(value = 1, message = "batch_size must be at least 1")
    @JsonProperty("batch_size")
    private Integer batchSize;

}
