package com.matketing.be.domain.content.client;

import com.matketing.be.domain.content.config.AiServerProperties;
import com.matketing.be.domain.content.dto.AiProcessUtteranceRequest;
import com.matketing.be.domain.content.dto.AiProcessUtteranceResponse;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.Duration;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Slf4j
@Component
public class AiContentClient {

    private final RestClient restClient;

    public AiContentClient(RestClient.Builder builder, AiServerProperties properties) {
        // 외부 AI 서버 장애가 Tomcat 요청 스레드를 오래 점유하지 않도록 설정값 기반 timeout을 적용한다.
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofSeconds(properties.timeoutSeconds()));
        requestFactory.setReadTimeout(Duration.ofSeconds(properties.timeoutSeconds()));
        this.restClient = builder
                .baseUrl(properties.baseUrl())
                .requestFactory(requestFactory)
                .build();
    }

    // FastAPI의 발화 처리 API를 호출하고 Spring 응답 DTO로 변환한다.
    // HTTP 오류, timeout, 응답 파싱 실패는 모두 사용자에게 AI_SERVER_FAILED로 노출한다.
    // 정상 HTTP 응답이어도 필수 필드가 빠져 있으면 실패로 본다.
    public AiProcessUtteranceResponse processUtterance(AiProcessUtteranceRequest request) {
        AiProcessUtteranceResponse response = sendProcessUtteranceRequest(request);
        validateRequiredFields(response);
        return response;
    }

    // 실제 HTTP POST 호출만 담당한다.
    // RestClientException은 4xx/5xx, 연결 실패, timeout 등 RestClient 계열 실패를 포괄한다.
    // 그 외 예외는 JSON 역직렬화 등 예상하지 못한 응답 처리 실패로 분류해 로그 키를 다르게 남긴다.
    private AiProcessUtteranceResponse sendProcessUtteranceRequest(AiProcessUtteranceRequest request) {
        try {
            // Spring은 텍스트 생성 트리거와 응답 반영만 담당하고, keyword/draft/photo/video 생성은 FastAPI에 위임한다.
            return restClient.post()
                    .uri("/ai/sessions/{sessionId}/process-utterance", request.sessionId())
                    .body(request)
                    .retrieve()
                    .body(AiProcessUtteranceResponse.class);
        } catch (RestClientException exception) {
            log.warn(
                    "content.ai.process-utterance.failed: FastAPI request failed. sessionId={}",
                    request.sessionId(),
                    exception
            );
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED, exception);
        } catch (Exception exception) {
            log.warn(
                    "content.ai.process-utterance.invalid-response: response parsing failed. sessionId={}",
                    request.sessionId(),
                    exception
            );
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED, exception);
        }
    }

    // Spring이 이후 Redis와 API 응답에서 반드시 필요로 하는 최소 필드를 검증한다.
    // guide_text/caption은 처리 중 응답이나 FastAPI 정책에 따라 null일 수 있으므로 여기서는 필수로 보지 않는다.
    private void validateRequiredFields(AiProcessUtteranceResponse response) {
        if (response == null || response.sessionId() == null) {
            // 명세상 필수 필드가 없으면 정상 HTTP 응답이어도 AI 서버 실패로 취급한다.
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED);
        }
    }

}
