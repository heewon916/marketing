package com.matketing.be.domain.content.client;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.matketing.be.domain.content.dto.LlamaIntentResponse;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.Duration;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Slf4j
@Component
public class LlamaIntentClient {

    private static final String SYSTEM_PROMPT = """
            당신은 카페 사장님을 돕는 친절한 AI 어시스턴트입니다.
            사용자의 입력이 인스타그램 게시물(피드) 생성을 요청하거나 의도하는 것이라면 isCreatePost를 true로 설정하세요.
            단순한 일상 대화나 감정 표현이라면 isCreatePost를 false로 설정하고, 카페 사장님과 대화하듯 다정하고 친근한 답변을 reply에 작성하세요.
            반드시 JSON만 응답하세요. 예: {"isCreatePost":false,"reply":"오늘 많이 힘드셨군요. 잠깐 쉬어가셔도 괜찮아요."}
            """;

    private final RestClient restClient;
    private final ObjectMapper objectMapper;
    private final String model;

    public LlamaIntentClient(
            RestClient.Builder builder,
            ObjectMapper objectMapper,
            @Value("${spring.ai.ollama.base-url}") String baseUrl,
            @Value("${spring.ai.ollama.chat.model:local-model}") String model,
            @Value("${llama.intent.timeout-seconds:120}") long timeoutSeconds
    ) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofSeconds(timeoutSeconds));
        requestFactory.setReadTimeout(Duration.ofSeconds(timeoutSeconds));
        this.restClient = builder
                .baseUrl(baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl)
                .requestFactory(requestFactory)
                .build();
        this.objectMapper = objectMapper;
        this.model = model;
    }

    public LlamaIntentResponse classify(String utterance) {
        try {
            ChatCompletionResponse response = restClient.post()
                    .uri("/v1/chat/completions")
                    .body(new ChatCompletionRequest(
                            model,
                            List.of(
                                    new ChatMessage("system", SYSTEM_PROMPT),
                                    new ChatMessage("user", utterance)
                            ),
                            false,
                            96,
                            0.1
                    ))
                    .retrieve()
                    .body(ChatCompletionResponse.class);
            return parseIntent(response);
        } catch (RestClientException exception) {
            log.warn("llama.intent.request-failed", exception);
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED, exception);
        } catch (Exception exception) {
            log.warn("llama.intent.invalid-response", exception);
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED, exception);
        }
    }

    private LlamaIntentResponse parseIntent(ChatCompletionResponse response) throws JsonProcessingException {
        String content = response != null
                && response.choices() != null
                && !response.choices().isEmpty()
                && response.choices().getFirst().message() != null
                ? response.choices().getFirst().message().content()
                : null;

        if (content == null || content.isBlank()) {
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED);
        }

        String json = extractJsonObject(content);
        LlamaIntentResponse intent = objectMapper.readValue(json, LlamaIntentResponse.class);
        if (!intent.isCreatePost() && (intent.reply() == null || intent.reply().isBlank())) {
            return new LlamaIntentResponse(false, "괜찮아요. 잠시 숨 고르고 천천히 이야기해 주세요.");
        }
        return intent;
    }

    private String extractJsonObject(String content) {
        int start = content.indexOf('{');
        int end = content.lastIndexOf('}');
        if (start < 0 || end <= start) {
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED);
        }
        return content.substring(start, end + 1);
    }

    private record ChatCompletionRequest(
            String model,
            List<ChatMessage> messages,
            boolean stream,
            Integer max_tokens,
            Double temperature
    ) {
    }

    private record ChatMessage(String role, String content) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    private record ChatCompletionResponse(List<Choice> choices) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    private record Choice(ChatMessage message) {
    }
}
