package com.matketing.be.domain.notification.service;

import com.matketing.be.domain.notification.enums.NotificationType;
import java.util.UUID;
import org.springframework.stereotype.Component;

@Component
public class NotificationMessageResolver {

    public String resolveNotificationText(NotificationType type) {
        if (type == null) {
            return "맡케팅 알림입니다.";
        }

        switch (type) {
            case REMIND:
                return "오늘의 게시물을 올릴 시간이에요. AI로 홍보 콘텐츠를 만들어보세요.";
            case WEATHER_MENU:
                return "오늘 날씨에 어울리는 메뉴를 홍보해보세요. AI로 콘텐츠를 만들어볼까요?";
            case HOLIDAY_MENU:
                return "다가오는 공휴일에 맞춰 메뉴 홍보 콘텐츠를 준비해보세요.";
            case HOLIDAY_OPERATION:
                return "공휴일 영업 변경 사항을 고객에게 안내해보세요.";
            case WEEKLY_STATS:
                return "이번 주 인기 게시물을 확인하고 다음 홍보 전략을 준비해보세요.";
            case POSTING_SUCCESS:
                return "인스타그램 게시물 발행이 완료됐어요.";
            case POSTING_FAILED:
                return "인스타그램 게시물 발행에 실패했어요. 다시 시도해 주세요.";
            case POST_PROMOTION_REMINDER:
                return "지금이 인스타 조회수가 가장 잘 나오는 시간이에요 사장님! 가게 홍보 글을 올려볼까요?";
            default:
                return "맡케팅 알림입니다.";
        }
    }

    public String resolveWebUrl(NotificationType type, UUID referenceId) {
        return "/post-create";
    }
}
