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
import com.matketing.be.domain.content.client.S3VideoClient;
import com.matketing.be.domain.content.config.ContentProperties;
import com.matketing.be.domain.content.dto.AiProcessUtteranceResponse;
import com.matketing.be.domain.content.dto.AiWeatherRequest;
import com.matketing.be.domain.content.dto.ChatRequest;
import com.matketing.be.domain.content.dto.ChatResponse;
import com.matketing.be.domain.content.dto.ContentEditRequestDto;
import com.matketing.be.domain.content.dto.ContentEditResponseDto;
import com.matketing.be.domain.content.dto.ContentRequest;
import com.matketing.be.domain.content.dto.ContentResponse;
import com.matketing.be.domain.content.dto.ContentImageUrlsResponseDto;
import com.matketing.be.domain.content.dto.ContentRedisResult;
import com.matketing.be.domain.content.dto.SttResponse;
import com.matketing.be.domain.content.enums.ContentStatus;
import com.matketing.be.domain.content.redis.ContentRedisRepository;
import com.matketing.be.domain.content.redis.ContentRedisRepository.RedisImageValue;
import com.matketing.be.domain.content.repository.ContentRepository;
import com.matketing.be.domain.store.entity.OwnerPersonaEnumType;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.global.auth.jwt.AuthUser;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.mock.web.MockMultipartFile;

@ExtendWith(MockitoExtension.class)
class ContentServiceTest {

    private static final String USER_ID = "00000000-0000-0000-0000-000000000001";
    private static final UUID STORE_ID = UUID.fromString("00000000-0000-0000-0000-000000000002");
    private static final String REQUEST_ID = "9d5b4b52-78f2-4f7e-8c10-4a04bb5a6b1b";

    @Mock
    private ContentRepository contentRepository;

    @Mock
    private ClovaSttClient clovaSttClient;

    @Mock
    private AiContentClient aiContentClient;

    @Mock
    private S3VideoClient s3VideoClient;

    @Mock
    private ContentRedisRepository contentRedisRepository;

    @Mock
    private StoreRepository storeRepository;

    @Mock
    private WeatherContextProvider weatherService;

    private final ContentProperties contentProperties = new ContentProperties(600);

    private ContentService contentService;

    @BeforeEach
    void setUp() {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                new AuthUser(UUID.fromString(USER_ID), "instagram-user-id", "instagram-name", "https://profile.example/image.jpg"),
                null
        ));
        contentService = new ContentService(
                contentRepository,
                clovaSttClient,
                aiContentClient,
                s3VideoClient,
                contentRedisRepository,
                contentProperties,
                storeRepository,
                weatherService
        );
    }

    @AfterEach
    void tearDown() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void createTextContentThrowsEmptyUtteranceWhenBlank() {
        ChatRequest request = new ChatRequest(REQUEST_ID, " ");

        assertThatThrownBy(() -> contentService.createTextContent(request))
                .isInstanceOf(BusinessException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.EMPTY_UTTERANCE);
    }

    @Test
    void createTextContentCreatesRedisStateAndReturnsAiResultOnFirstRequest() {
        ChatRequest request = new ChatRequest(REQUEST_ID, "오늘 가게 찻잔을 자랑하고 싶어");
        Store store = mockStore();
        when(contentRedisRepository.setIdempotencyKeyIfAbsent(eq(USER_ID), eq(REQUEST_ID), any(), eq(Duration.ofSeconds(600))))
                .thenReturn(true);
        when(storeRepository.findFirstByUserId(UUID.fromString(USER_ID))).thenReturn(Optional.of(store));
        when(weatherService.getWeatherContext(eq(store), any(LocalDateTime.class))).thenReturn(AiWeatherRequest.empty());
        when(aiContentClient.processUtterance(any()))
                .thenReturn(new AiProcessUtteranceResponse(
                        "session-id",
                        "TEXT_GENERATED",
                        "예쁘게 찍어주세요!",
                        "따뜻한 차 한 잔 어떠세요?"
                ));

        ChatResponse response = contentService.createTextContent(request);

        assertThat(response.status()).isEqualTo(ContentStatus.TEXT_GENERATED);
        assertThat(response.guideText()).isEqualTo("예쁘게 찍어주세요!");
        assertThat(response.caption()).isEqualTo("따뜻한 차 한 잔 어떠세요?");
        verify(contentRedisRepository).createStartedContent(response.sessionId(), STORE_ID.toString(), request.utterance());
        verify(contentRedisRepository).updateTextGeneratedResult(
                response.sessionId(),
                "예쁘게 찍어주세요!",
                "따뜻한 차 한 잔 어떠세요?",
                ContentStatus.TEXT_GENERATED
        );
    }

    private Store mockStore() {
        Store store = org.mockito.Mockito.mock(Store.class);
        org.mockito.Mockito.when(store.getId()).thenReturn(STORE_ID);
        org.mockito.Mockito.when(store.getOwnerPersona()).thenReturn(OwnerPersonaEnumType.aesthetic);
        return store;
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

        ChatResponse response = contentService.createTextContent(request);

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

        ChatResponse response = contentService.createTextContent(request);

        assertThat(response.sessionId()).isEqualTo("existing-session");
        assertThat(response.status()).isEqualTo(ContentStatus.STARTED);
        assertThat(response.guideText()).isNull();
        assertThat(response.caption()).isNull();
        verify(aiContentClient, never()).processUtterance(any());
    }

    @Test
    void createCaptionContextReturnsStoreUtterancePersonaDateAndWeather() {
        Store store = mockStore();
        AiWeatherRequest weather = new AiWeatherRequest(
                18.5,
                0.0,
                "맑음",
                45,
                2.5,
                85,
                35,
                12.0,
                63,
                null,
                null
        );
        when(storeRepository.findById(STORE_ID)).thenReturn(Optional.of(store));
        when(weatherService.getWeatherContext(eq(store), any(LocalDateTime.class))).thenReturn(weather);

        ContentResponse response = contentService.createCaptionContext(
                new ContentRequest(null, STORE_ID.toString(), "오늘 가게 찻잔을 자랑하고 싶어")
        );

        assertThat(response.storeId()).isEqualTo(STORE_ID.toString());
        assertThat(response.utterance()).isEqualTo("오늘 가게 찻잔을 자랑하고 싶어");
        assertThat(response.ownerPersona()).isEqualTo("aesthetic");
        assertThat(response.date()).isNotBlank();
        assertThat(response.weather()).isEqualTo(weather);
    }

    @Test
    void getContentImagesReturnsPhotoUrlsFromRedisBySessionId() {
        UUID sessionId = UUID.randomUUID();
        when(contentRedisRepository.getPhotoUrls(sessionId.toString()))
                .thenReturn(java.util.List.of(
                        new RedisImageValue("photo:1", "/ai-finals/%s/final-001.jpg".formatted(sessionId)),
                        new RedisImageValue("photo:2", "/ai-finals/%s/final-002.jpg".formatted(sessionId))
                ));

        ContentImageUrlsResponseDto response = contentService.getContentImages(sessionId);

        assertThat(response.sessionId()).isEqualTo(sessionId);
        assertThat(response.imageUrl())
                .extracting(ContentImageUrlsResponseDto.ImageUrlItem::imageUrl)
                .containsExactly(
                        "/ai-finals/%s/final-001.jpg".formatted(sessionId),
                        "/ai-finals/%s/final-002.jpg".formatted(sessionId)
                );
    }

    @Test
    void updateContentUpdatesCaptionInRedisBySessionId() {
        UUID sessionId = UUID.randomUUID();
        ContentEditRequestDto request = new ContentEditRequestDto("수정된 캡션");
        when(contentRedisRepository.updateCaption(eq(sessionId.toString()), eq(request.caption()), any())).thenReturn(true);

        ContentEditResponseDto response = contentService.updateContent(sessionId, request);

        assertThat(response.sessionId()).isEqualTo(sessionId);
        assertThat(response.caption()).isEqualTo("수정된 캡션");
        assertThat(response.updatedAt()).isNotNull();
        verify(contentRedisRepository).updateCaption(eq(sessionId.toString()), eq("수정된 캡션"), any());
    }

    @Test
    void updateContentThrowsContentNotFoundWhenRedisSessionDoesNotExist() {
        UUID sessionId = UUID.randomUUID();
        ContentEditRequestDto request = new ContentEditRequestDto("수정된 캡션");
        when(contentRedisRepository.updateCaption(eq(sessionId.toString()), eq(request.caption()), any())).thenReturn(false);

        assertThatThrownBy(() -> contentService.updateContent(sessionId, request))
                .isInstanceOf(BusinessException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.CONTENT_NOT_FOUND);
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
