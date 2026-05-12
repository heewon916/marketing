package com.matketing.be.domain.analytic.controller;

import com.matketing.be.domain.analytic.dto.AchievementResponse;
import com.matketing.be.domain.analytic.dto.ReachResponse;
import com.matketing.be.domain.analytic.dto.VisitIntentResponse;
import com.matketing.be.domain.analytic.service.AnalyticsQueryService;
import com.matketing.be.global.auth.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;

@Slf4j
@RestController
@RequestMapping("/api/v1/analytics")
@RequiredArgsConstructor
@Tag(name = "Analytics", description = "주간 통계 데이터 조회 API")
public class AnalyticsController {

        private final AnalyticsQueryService analyticsQueryService;

        /**
         * 주간 가게 노출 수를 조회한다.
         * week_start는 yyyy-MM-dd 형식의 주차 시작일이다.
         */
        @Operation(summary = "주간 가게 노출 수 조회", description = "week_start 기준 주간 total_reach를 조회합니다.")
        @GetMapping("/reach")
        public ResponseEntity<ReachResponse> getReach(
                        @AuthenticationPrincipal AuthUser authUser,
                        @RequestParam("week_start") LocalDate weekStart) {
                return ResponseEntity.ok(
                                analyticsQueryService.getReach(authUser.getId(), weekStart));
        }

        /**
         * 주간 실질 방문 의사 지수를 조회한다.
         * 저장 수와 공유 수를 도달 수로 나누어 계산한다.
         */
        @Operation(summary = "주간 실질 방문 의사 지수 조회", description = "저장 수와 공유 수를 도달 수로 나눈 방문 의사 지수를 조회합니다.")
        @GetMapping("/visit-intent")
        public ResponseEntity<VisitIntentResponse> getVisitIntent(
                        @AuthenticationPrincipal AuthUser authUser,
                        @RequestParam("week_start") LocalDate weekStart) {
                return ResponseEntity.ok(
                                analyticsQueryService.getVisitIntent(authUser.getId(), weekStart));
        }

        /**
         * 주간 포스팅 달성률을 조회한다.
         * 실제 발행 게시물 수와 목표 게시물 수를 기준으로 계산한다.
         */
        @Operation(summary = "주간 포스팅 달성률 조회", description = "목표 게시물 수 대비 실제 발행 게시물 수의 달성률을 조회합니다.")
        @GetMapping("/achievement")
        public ResponseEntity<AchievementResponse> getAchievement(
                        @AuthenticationPrincipal AuthUser authUser,
                        @RequestParam("week_start") LocalDate weekStart) {
                return ResponseEntity.ok(
                                analyticsQueryService.getAchievement(authUser.getId(), weekStart));
        }
}
