package com.matketing.be.domain.content.service;

import com.matketing.be.domain.content.client.AiContentClient;
import com.matketing.be.domain.content.client.ClovaSttClient;
import com.matketing.be.domain.content.config.ContentProperties;
import com.matketing.be.domain.content.dto.AiProcessUtteranceRequest;
import com.matketing.be.domain.content.dto.AiProcessUtteranceResponse;
import com.matketing.be.domain.content.dto.AiWeatherRequest;
import com.matketing.be.domain.content.dto.ChatRequest;
import com.matketing.be.domain.content.dto.ChatResponse;
import com.matketing.be.domain.content.dto.ContentEditRequestDto;
import com.matketing.be.domain.content.dto.ContentEditResponseDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteResponseDto;
import com.matketing.be.domain.content.dto.ContentImageUrlsResponseDto;
import com.matketing.be.domain.content.dto.ContentRedisResult;
import com.matketing.be.domain.content.dto.ContentResponseDto;
import com.matketing.be.domain.content.dto.SttResponse;
import com.matketing.be.domain.content.entity.Content;
import com.matketing.be.domain.content.entity.ContentImage;
import com.matketing.be.domain.content.enums.ContentStatus;
import com.matketing.be.domain.content.redis.ContentRedisRepository;
import com.matketing.be.domain.content.repository.ContentImageRepository;
import com.matketing.be.domain.content.repository.ContentRepository;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.Duration;
import java.time.LocalDate;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Service
@RequiredArgsConstructor
public class ContentService {

    private static final Set<String> ALLOWED_AUDIO_CONTENT_TYPES = Set.of(
            "audio/wav",
            "audio/x-wav",
            "audio/mpeg",
            "audio/mp3",
            "audio/mp4",
            "audio/webm",
            "audio/ogg"
    );
    private static final Set<String> ALLOWED_AUDIO_EXTENSIONS = Set.of(
            "wav",
            "mp3",
            "m4a",
            "mp4",
            "webm",
            "ogg"
    );
    private static final String TEXT_RECOGNIZED = "TEXT_RECOGNIZED";

    private final ContentRepository contentRepository;
    private final ContentImageRepository contentImageRepository;
    private final ClovaSttClient clovaSttClient;
    private final AiContentClient aiContentClient;
    private final ContentRedisRepository contentRedisRepository;
    private final ContentProperties contentProperties;
    private final StoreRepository storeRepository;


    /**
     * [사용자 발화 처리] /api/v1/contents/stt 핵심 비즈니스 로직
     * - 사용자 음성 파일 -> 텍스트 처리
     * 역할: 파일 정책 검증, Clova 호출
     * 반환: TEXT_RECOGNIZED로 고정
     * @param audioFile
     * @return
     */
    public SttResponse recognizeSpeech(MultipartFile audioFile) {
        validateAudioFile(audioFile); // Clova 호출 전에 Spring에서 파일 유효성을 먼저 차단해 외부 API 비용과 불필요한 장애를 줄인다.

        String utterance = clovaSttClient.recognize(audioFile);
        return new SttResponse(utterance, TEXT_RECOGNIZED);
    }


    /**
     * [게시물 생성 로직] api/v1/contents/{sessionId}/caption 핵심 비즈니스 로직
     * @param request request_id, 최종 utterance
     * @param userId // TODO 체크 필요한 값
     * @return
     */
    public ChatResponse createTextContent(ChatRequest request, String userId) {
        // 1. utterance empty 검사
        if (request.utterance() == null || request.utterance().isBlank()) {
            throw new BusinessException(ErrorCode.EMPTY_UTTERANCE);
        }

        // 2. request_id + session_id 기준으로 Redis 멱등성 key 생성
        String requestId = request.requestId();
        String sessionId = UUID.randomUUID().toString();
        Duration ttl = Duration.ofSeconds(contentProperties.idempotencyTtlSeconds()); // 10분 동안은 같은 request_id는 중복 처리된다
        boolean firstRequest = contentRedisRepository.setIdempotencyKeyIfAbsent(userId, requestId, sessionId, ttl); // Redis SET NX EX

        // 3. 중복 요청일 경우 (처리 중, 처리 완료된)
        if (!firstRequest) {

            // 3-1. fast api 호출 없이, redis 값 전달
            String existingSessionId = contentRedisRepository.getSessionIdByRequestId(userId, requestId);

            // (예외) 매핑된 session_id가 없을 경우: 만료 시점의 race condition 원인
            if (existingSessionId == null || existingSessionId.isBlank()) {
                throw new BusinessException(ErrorCode.AI_SERVER_FAILED);
            }

            // 3-2. 이미 결과가 존재 -> 동일 request_id 재요쳥에도 동일 결과 리턴
            ContentRedisResult existingResult = contentRedisRepository.getContentResult(existingSessionId);
            return new ChatResponse(
                    existingSessionId,
                    existingResult.status(),
                    existingResult.guideText(),
                    existingResult.caption()
            );
        }

        // 4. 최초 요청일 경우: Redis에 contents:{sessionId}/ utterance만 초기화한다.
        // TODO FastAPI는 sessionId로 검색하고, utterance는 GET만 진행한다.
        contentRedisRepository.createStartedContent(sessionId, request.utterance());

        // 5. store 정보를 들고 온다
        StoreContext storeContext = getStoreContext(userId);

        // 6. TODO 날씨 API로부터 필요한 데이터를 들고 온다

        // 7. ai/sessions/{session_id}/process_utterance API를 호출하는 곳이다
        AiProcessUtteranceResponse aiResponse = aiContentClient.processUtterance(new AiProcessUtteranceRequest(
                sessionId,
                storeContext.storeId(),
                request.utterance(),
                storeContext.ownerPersona(),
                LocalDate.now().toString(),
                // TODO: 날씨 Open API 완료 후 실제 temperature/precipitation/cloud_cover 등으로 채운다.
                AiWeatherRequest.empty()
        ));

        // 8. AI서버의 응답을 파싱해서 프론트에 응답함과 동시에, putIfAbsent패턴으로 Redis를 갱신한다
        ContentStatus status = parseAiStatus(aiResponse.status());
        contentRedisRepository.updateTextGeneratedResult(
                sessionId,
                aiResponse.guideText(),
                aiResponse.caption(),
                status
        );

        return new ChatResponse(sessionId, status, aiResponse.guideText(), aiResponse.caption());
    }

    /**
     * [게시물 이미지 조회] /api/v1/contents/{content_id}/images 핵심 비즈니스 로직
     * @param contentId
     * @return
     */
    @Transactional(readOnly = true)
    public ContentImageUrlsResponseDto getContentImages(Long contentId) {
        Content content = getContentWithRelations(contentId);

        return new ContentImageUrlsResponseDto(
                content.getImages().stream()
                        .map(ContentImage::getS3Key)
                        .toList()
        );
    }

    /**
     * [게시물 이미지 삭제] /api/v1/contents/{content_id}/images/{image_id} 핵심 비즈니스 로직
     * @param contentId
     * @param imageId
     * @return
     */
    @Transactional
    public ContentImageDeleteResponseDto deleteContentImage(Long contentId, UUID imageId) {
        // TODO 이미지 정보 삭제는 redis에서 이루어진다. 이때 contentId가 필요한 것이 맞는지 sessionId가 필요한 것이 맞는지 확인이 필요하다
        findContentById(contentId);

        ContentImage contentImage = contentImageRepository.findByIdAndContent_Id(imageId, contentId)
                .orElseThrow(() -> new BusinessException(ErrorCode.CONTENT_IMAGE_NOT_FOUND));

        contentImageRepository.delete(contentImage);

        long remainingImages = contentImageRepository.countByContent_Id(contentId);
        return new ContentImageDeleteResponseDto(true, remainingImages);
    }

    /**
     * [게시물 내용 조회] /api/v1/contents/{content_id} 핵심 비즈니스 로직
     * @param contentId
     * @return
     */
    @Transactional(readOnly = true)
    public ContentResponseDto getContent(Long contentId) {
        return ContentResponseDto.from(getContentWithRelations(contentId));
    }

    /**
     * [게시물 텍스트 갱신] /api/v1/contents/{content_id}/edit 핵심 비즈니스 로직
     * @param contentId
     * @param requestDto 캡션만 수정 가능하다.
     * @return 수정된
     */
    @Transactional
    public ContentEditResponseDto updateContent(Long contentId, ContentEditRequestDto requestDto) {
        Content content = findContentById(contentId);

        // 현재 스키마에는 status/hashtags/updatedAt이 없어 caption만 수정한다.
        content.updateCaption(requestDto.caption());

        return ContentEditResponseDto.from(content);
    }

    //============================================
    // 여기서부터는 부가 로직이다.
    //============================================
    private Content findContentById(Long contentId) {
        return contentRepository.findById(contentId)
                .orElseThrow(() -> new BusinessException(ErrorCode.CONTENT_NOT_FOUND));
    }

    private Content getContentWithRelations(Long contentId) {
        return contentRepository.findWithImagesAndVideoRecordingsById(contentId)
                .orElseThrow(() -> new BusinessException(ErrorCode.CONTENT_NOT_FOUND));
    }

    // STT에 전달할 수 있는 오디오 파일인지 사전 검증한다.
    // content-type을 우선 신뢰하되, 모바일/브라우저 환경에서 content-type이 빠질 수 있어 확장자를 보조 기준으로 허용한다.
    // 둘 다 허용 목록에 없거나 파일이 비어 있으면 INVALID_AUDIO_FILE로 통일한다.
    private void validateAudioFile(MultipartFile audioFile) {
        if (audioFile == null || audioFile.isEmpty()) {
            throw new BusinessException(ErrorCode.INVALID_AUDIO_FILE);
        }

        // 클라이언트/브라우저별 content-type 누락 가능성을 고려해 확장자를 보조 검증으로 허용한다.
        String contentType = audioFile.getContentType();
        if (contentType != null && ALLOWED_AUDIO_CONTENT_TYPES.contains(contentType.toLowerCase(Locale.ROOT))) {
            return;
        }

        String filename = audioFile.getOriginalFilename();
        if (filename != null) {
            int dotIndex = filename.lastIndexOf('.');
            if (dotIndex >= 0 && dotIndex < filename.length() - 1) {
                String extension = filename.substring(dotIndex + 1).toLowerCase(Locale.ROOT);
                if (ALLOWED_AUDIO_EXTENSIONS.contains(extension)) {
                    return;
                }
            }
        }

        throw new BusinessException(ErrorCode.INVALID_AUDIO_FILE);
    }

    /**
     * 캡션 생성 시, store 정보 조회에 사용된다.
     * TODO userId 값에 따라 store 정보를 제대로 들고 오는지 확인해야 한다
     * @param userId
     * @return
     */
    private StoreContext getStoreContext(String userId) {
        Optional<Store> store = parseUuid(userId)
                .flatMap(storeRepository::findFirstByUserId);

        if (store.isEmpty()) {
            // TODO: 실제 인증 적용 후 매장 미등록 사용자를 어떤 에러로 처리할지 정책화한다.
            return new StoreContext("00000000-0000-0000-0000-000000000000", "aesthetic");
        }

        Store foundStore = store.get();
        String ownerPersona = foundStore.getOwnerPersona();
        if (ownerPersona == null || ownerPersona.isBlank()) {
            ownerPersona = "aesthetic";
        }
        return new StoreContext(foundStore.getId().toString(), ownerPersona);
    }

    private Optional<UUID> parseUuid(String value) {
        try {
            return Optional.of(UUID.fromString(value));
        } catch (IllegalArgumentException exception) {
            return Optional.empty();
        }
    }

    // FastAPI가 돌려준 상태 문자열을 Spring 표준 enum으로 변환한다.
    // 알 수 없는 상태값은 이후 Redis/API 응답을 오염시키지 않도록 AI_SERVER_FAILED로 처리한다.
    private ContentStatus parseAiStatus(String status) {
        try {
            // 외부 응답은 photo-edited 같은 하이픈 표기가 섞일 수 있어 enum 변환 지점에서 정규화한다.
            return ContentStatus.fromExternal(status);
        } catch (IllegalArgumentException exception) {
            throw new BusinessException(ErrorCode.AI_SERVER_FAILED, exception);
        }
    }

    private record StoreContext(
            String storeId,
            String ownerPersona
    ) {
    }
}
