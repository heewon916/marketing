package com.matketing.be.domain.notification.dto;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class NotificationHistoryResponse {
    
    private List<NotificationHistoryItemResponse> notifications;
    private long total;
    private int page;
    private int size;
}
