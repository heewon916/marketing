package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.enums.NotificationType;

public class NotificationTitleResolver {

    // 알림 타입에 맞는 알림 제목을 반환한다.
    public static String resolve(NotificationType type) {
        if (type == null) {
            return "맡케팅 알림";
        }
        return switch (type) {
            case REMIND -> "게시물 올릴 시간이에요";
            case WEATHER_MENU -> "오늘 날씨에 맞는 메뉴를 홍보해보세요";
            case HOLIDAY_MENU -> "공휴일 메뉴 홍보를 준비해보세요";
            case HOLIDAY_OPERATION -> "공휴일 영업 변경을 안내해보세요";
            case WEEKLY_STATS -> "이번 주 통계가 도착했어요";
            case POSTING_SUCCESS -> "게시물이 발행됐어요";
            case POSTING_FAILED -> "게시물 발행에 실패했어요";
            default -> "맡케팅 알림";
        };
    }
}
