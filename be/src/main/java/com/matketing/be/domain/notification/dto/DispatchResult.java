package com.matketing.be.domain.notification.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class DispatchResult {
    private int dispatchedCount;
    private int failedCount;
}
