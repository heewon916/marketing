package com.matketing.be.domain.onboarding.util;

import com.matketing.be.domain.store.entity.CategoryEnumType;
import com.matketing.be.domain.store.entity.Menu;

import java.util.List;

public class CategoryInferenceUtil {

    /**
     * 메뉴 이름 목록을 분석하여 가장 확률이 높은 업종(Category)을 유추합니다.
     * 상세한 키워드 사전과 가중치를 사용하여 정확도를 높였습니다.
     */
    public static CategoryEnumType guessCategory(List<Menu> menus) {
        if (menus == null || menus.isEmpty()) {
            return CategoryEnumType.카페; // 기본값
        }

        int cafeScore = 0;
        int pubScore = 0;
        int bakeryScore = 0;
        int restaurantScore = 0;

        for (Menu m : menus) {
            if (m.getName() == null) continue;
            String name = m.getName().replaceAll("\\s+", "").toLowerCase(); // 공백 제거 후 소문자 변환

            // 1. 카페 키워드
            if (name.contains("커피") || name.contains("아메리카노") || name.contains("라떼") ||
                name.contains("에스프레소") || name.contains("스무디") || name.contains("에이드") ||
                name.contains("프라푸치노") || name.contains("콜드브루") || name.contains("밀크티")) {
                cafeScore += 2;
            } else if (name.contains("차") || name.contains("티")) {
                cafeScore += 1;
            }

            // 2. 주점 키워드
            if (name.contains("소주") || name.contains("맥주") || name.contains("하이볼") ||
                name.contains("안주") || name.contains("생맥") || name.contains("호프") ||
                name.contains("칵테일") || name.contains("사케") || name.contains("마른안주")) {
                pubScore += 2;
            } else if (name.contains("탕") || name.contains("구이") || name.contains("튀김")) {
                pubScore += 1;
            }

            // 3. 제과점 키워드
            if (name.contains("빵") || name.contains("케이크") || name.contains("크루아상") ||
                name.contains("마카롱") || name.contains("샌드위치") || name.contains("베이글") ||
                name.contains("스콘") || name.contains("타르트") || name.contains("바게트") ||
                name.contains("휘낭시에") || name.contains("마들렌") || name.contains("쿠키")) {
                bakeryScore += 2;
            }

            // 4. 식당(음식점) 키워드
            if (name.contains("밥") || name.contains("찌개") || name.contains("국") ||
                name.contains("면") || name.contains("파스타") || name.contains("고기") ||
                name.contains("돈까스") || name.contains("피자") || name.contains("샐러드") ||
                name.contains("볶음") || name.contains("정식") || name.contains("초밥")) {
                restaurantScore += 2;
            }
        }

        // 최고 점수 계산
        int maxScore = Math.max(Math.max(cafeScore, pubScore), Math.max(bakeryScore, restaurantScore));

        // 매칭되는 키워드가 전혀 없거나 모두 0점일 경우 기본값
        if (maxScore == 0) {
            return CategoryEnumType.카페;
        }

        // 점수가 가장 높은 카테고리 반환 (동점일 경우 우선순위: 식당 > 카페 > 주점 > 제과점)
        if (maxScore == restaurantScore) return CategoryEnumType.식당;
        if (maxScore == cafeScore) return CategoryEnumType.카페;
        if (maxScore == pubScore) return CategoryEnumType.주점;
        if (maxScore == bakeryScore) return CategoryEnumType.제과점;

        return CategoryEnumType.카페;
    }
}
