package com.matketing.be.domain.content.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.matketing.be.domain.content.client.AiContentClient;
import com.matketing.be.domain.content.client.ClovaSttClient;
import com.matketing.be.domain.content.config.ContentProperties;
import com.matketing.be.domain.content.dto.AiProcessUtteranceResponse;
import com.matketing.be.domain.content.dto.ChatRequest;
import com.matketing.be.domain.content.dto.ChatResponse;
import com.matketing.be.domain.content.dto.ContentRedisResult;
import com.matketing.be.domain.content.dto.SttResponse;
import com.matketing.be.domain.content.enums.ContentStatus;
import com.matketing.be.domain.content.redis.ContentRedisRepository;
import com.matketing.be.domain.content.repository.ContentImageRepository;
import com.matketing.be.domain.content.repository.ContentRepository;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.Duration;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;

@ExtendWith(MockitoExtension.class)
class ContentServiceTest {

    private static final String USER_ID = "user-1";
    private static final String REQUEST_ID = "9d5b4b52-78f2-4f7e-8c10-4a04bb5a6b1b";

    @Mock
    private ContentRepository contentRepository;

    @Mock
    private ContentImageRepository contentImageRepository;

    @Mock
    private ClovaSttClient clovaSttClient;

    @Mock
    private AiContentClient aiContentClient;

    @Mock
    private ContentRedisRepository contentRedisRepository;

    @Mock
    private StoreRepository storeRepository;

    private final ContentProperties contentProperties = new ContentProperties(600);

    private ContentService contentService;

    @BeforeEach
    void setUp() {
        contentService = new ContentService(
                contentRepository,
                contentImageRepository,
                clovaSttClient,
                aiContentClient,
                contentRedisRepository,
                contentProperties,
                storeRepository
        );
    }

    @Test
    void createTextContentThrowsEmptyUtteranceWhenBlank() {
        ChatRequest request = new ChatRequest(REQUEST_ID, " ");

        assertThatThrownBy(() -> contentService.createTextContent(request, USER_ID))
                .isInstanceOf(BusinessException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.EMPTY_UTTERANCE);
    }

    @Test
    void createTextContentCreatesRedisStateAndReturnsAiResultOnFirstRequest() {
        ChatRequest request = new ChatRequest(REQUEST_ID, "오늘 가게 찻잔을 자랑하고 싶어");
        when(contentRedisRepository.setIdempotencyKeyIfAbsent(eq(USER_ID), eq(REQUEST_ID), any(), eq(Duration.ofSeconds(600))))
                .thenReturn(true);
        when(aiContentClient.processUtterance(any()))
                .thenReturn(new AiProcessUtteranceResponse(
                        "session-id",
                        "TEXT_GENERATED",
                        "예쁘게 찍어주세요!",
                        "따뜻한 차 한 잔 어떠세요?"
                ));

        ChatResponse response = contentService.createTextContent(request, USER_ID);

        assertThat(response.status()).isEqualTo(ContentStatus.TEXT_GENERATED);
        assertThat(response.guideText()).isEqualTo("예쁘게 찍어주세요!");
        assertThat(response.caption()).isEqualTo("따뜻한 차 한 잔 어떠세요?");
        verify(contentRedisRepository).createStartedContent(response.sessionId(), request.utterance());
        verify(contentRedisRepository).updateTextGeneratedResult(
                response.sessionId(),
                "예쁘게 찍어주세요!",
                "따뜻한 차 한 잔 어떠세요?",
                ContentStatus.TEXT_GENERATED
        );
    }

    @Test
    void createTextContentReturnsCachedResultWithoutAiCallOnDuplicateRequest() {
        ChatRequest request = new ChatRequest(REQUEST_ID, "오늘 가게 찻잔을 자랑하고 싶어");
        when(contentRedisRepository.setIdempotencyKeyIfAbsent(eq(USER_ID), eq(REQUEST_ID), any(), eq(Duration.ofSeconds(600))))
                .thenReturn(false);
        when(contentRedisRepository.getSessionIdByRequestId(USER_ID, REQUEST_ID)).thenReturn("existing-session");
        when(contentRedisRepository.getContentResult("existing-session"))
                .thenReturn(new ContentRedisResult(
                        "existing-session",
                        ContentStatus.TEXT_GENERATED,
                        "기존 가이드",
                        "기존 캡션"
                ));

        ChatResponse response = contentService.createTextContent(request, USER_ID);

        assertThat(response.sessionId()).isEqualTo("existing-session");
        assertThat(response.status()).isEqualTo(ContentStatus.TEXT_GENERATED);
        assertThat(response.guideText()).isEqualTo("기존 가이드");
        assertThat(response.caption()).isEqualTo("기존 캡션");
        verify(aiContentClient, never()).processUtterance(any());
    }

    @Test
    void createTextContentReturnsStartedWhenDuplicateRequestIsStillProcessing() {
        ChatRequest request = new ChatRequest(REQUEST_ID, "오늘 가게 찻잔을 자랑하고 싶어");
        when(contentRedisRepository.setIdempotencyKeyIfAbsent(eq(USER_ID), eq(REQUEST_ID), any(), eq(Duration.ofSeconds(600))))
                .thenReturn(false);
        when(contentRedisRepository.getSessionIdByRequestId(USER_ID, REQUEST_ID)).thenReturn("existing-session");
        when(contentRedisRepository.getContentResult("existing-session"))
                .thenReturn(new ContentRedisResult("existing-session", ContentStatus.STARTED, null, null));

        ChatResponse response = contentService.createTextContent(request, USER_ID);

        assertThat(response.sessionId()).isEqualTo("existing-session");
        assertThat(response.status()).isEqualTo(ContentStatus.STARTED);
        assertThat(response.guideText()).isNull();
        assertThat(response.caption()).isNull();
        verify(aiContentClient, never()).processUtterance(any());
    }

    @Test
    void recognizeSpeechThrowsInvalidAudioWhenEmpty() {
        MockMultipartFile file = new MockMultipartFile("audio_file", "empty.wav", "audio/wav", new byte[0]);

        assertThatThrownBy(() -> contentService.recognizeSpeech(file))
                .isInstanceOf(BusinessException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.INVALID_AUDIO_FILE);
    }

    @Test
    void recognizeSpeechReturnsTextRecognized() {
        MockMultipartFile file = new MockMultipartFile("audio_file", "voice.wav", "audio/wav", "data".getBytes());
        when(clovaSttClient.recognize(file)).thenReturn("인식된 문장");

        SttResponse response = contentService.recognizeSpeech(file);

        assertThat(response.utterance()).isEqualTo("인식된 문장");
        assertThat(response.status()).isEqualTo("TEXT_RECOGNIZED");
    }
}
