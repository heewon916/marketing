package com.matketing.be.domain.content.client;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.matketing.be.domain.content.dto.LlamaIntentResponse;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.Map;
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
            @Value("${spring.ai.ollama.base-url:${CHAT_MODEL_BASE_URL}}") String baseUrl,
            @Value("${spring.ai.ollama.chat.model:${OLLAMA_MODEL:local-model}}") String model,
            @Value("${llama.intent.timeout-seconds:120}") long timeoutSeconds
    ) {
        if (baseUrl == null || baseUrl.isBlank()) {
            throw new IllegalStateException("CHAT_MODEL_BASE_URL is required for llama intent classification.");
        }
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
                            Map.of("type", "json_object"),
                            false,
                            96,
                            0.0
                    ))
                    .retrieve()
                    .body(ChatCompletionResponse.class);
            return parseIntent(response, utterance);
        } catch (RestClientException exception) {
            log.warn("llama.intent.request-failed", exception);
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED, exception);
        } catch (Exception exception) {
            log.warn("llama.intent.invalid-response", exception);
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED, exception);
        }
    }

    private LlamaIntentResponse parseIntent(ChatCompletionResponse response, String utterance) throws JsonProcessingException {
        String content = response != null
                && response.choices() != null
                && !response.choices().isEmpty()
                && response.choices().getFirst().message() != null
                ? response.choices().getFirst().message().content()
                : null;

        if (content == null || content.isBlank()) {
            log.warn("llama.intent.empty-response");
            return fallbackIntent(utterance);
        }

        String json = extractJsonObject(content, utterance);
        LlamaIntentResponse intent = objectMapper.readValue(json, LlamaIntentResponse.class);
        if (!intent.isCreatePost() && (intent.reply() == null || intent.reply().isBlank())) {
            return new LlamaIntentResponse(false, "괜찮아요. 잠시 숨 고르고 천천히 이야기해 주세요.");
        }
        return intent;
    }

    private String extractJsonObject(String content, String utterance) {
        int start = content.indexOf('{');
        int end = content.lastIndexOf('}');
        if (start < 0 || end <= start) {
            log.warn("llama.intent.non-json-response: contentPreview={}", preview(content));
            return objectToJson(fallbackIntent(utterance));
        }
        return content.substring(start, end + 1);
    }

    private LlamaIntentResponse fallbackIntent(String utterance) {
        String normalized = utterance == null ? "" : utterance.toLowerCase(Locale.ROOT);
        boolean createPost = List.of(
                "인스타", "instagram", "게시물", "피드", "캡션", "caption", "릴스", "reels",
                "홍보", "포스팅", "post", "올려", "올릴", "만들", "작성", "소개"
        ).stream().anyMatch(normalized::contains);

        if (createPost) {
            return new LlamaIntentResponse(true, "");
        }
        return new LlamaIntentResponse(false, "괜찮아요. 오늘 많이 지치셨다면 잠깐 쉬어가셔도 좋아요.");
    }

    private String objectToJson(LlamaIntentResponse response) {
        try {
            return objectMapper.writeValueAsString(response);
        } catch (JsonProcessingException exception) {
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED, exception);
        }
    }

    private String preview(String content) {
        String compact = content.replaceAll("\\s+", " ").trim();
        return compact.length() <= 200 ? compact : compact.substring(0, 200);
    }

    private record ChatCompletionRequest(
            String model,
            List<ChatMessage> messages,
            Map<String, String> response_format,
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
