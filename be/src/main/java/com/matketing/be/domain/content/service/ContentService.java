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

    // 사용자 음성 파일을 텍스트 발화로 변환하는 STT 유스케이스다.
    // Spring은 파일 정책 검증과 Clova 호출까지만 담당하고, 반환 상태는 STT 전용 상태인 TEXT_RECOGNIZED로 고정한다.
    public SttResponse recognizeSpeech(MultipartFile audioFile) {
        // Clova 호출 전에 Spring에서 파일 유효성을 먼저 차단해 외부 API 비용과 불필요한 장애를 줄인다.
        validateAudioFile(audioFile);

        String utterance = clovaSttClient.recognize(audioFile);
        return new SttResponse(utterance, TEXT_RECOGNIZED);
    }

    // 최종 발화로 guide_text/caption 생성을 요청하는 핵심 유스케이스다.
    // 처리 순서:
    // 1. utterance 필수값을 검증한다.
    // 2. request_id 기준 Redis 멱등성 key를 생성해 최초 요청과 중복 요청을 나눈다.
    // 3. 최초 요청이면 contents:{session_id} Hash를 STARTED 상태로 초기화하고 FastAPI를 호출한다.
    // 4. FastAPI 응답의 텍스트 결과를 Redis에 반영한 뒤 프론트 응답으로 반환한다.
    // 5. 중복 요청이면 FastAPI를 재호출하지 않고 기존 Redis 결과 또는 STARTED 상태를 반환한다.
    public ChatResponse createTextContent(ChatRequest request, String userId) {
        if (request.utterance() == null || request.utterance().isBlank()) {
            throw new BusinessException(ErrorCode.EMPTY_UTTERANCE);
        }

        String requestId = request.requestId();
        String sessionId = UUID.randomUUID().toString();
        // TTL 동안만 같은 request_id를 같은 session_id로 묶는다. 기본값 600은 600ms가 아니라 600초다.
        // TTL 만료 후 같은 request_id가 다시 오면 새 요청으로 취급될 수 있다.
        Duration ttl = Duration.ofSeconds(contentProperties.idempotencyTtlSeconds());

        // Redis SET NX EX를 한 번에 실행해 같은 request_id가 동시에 들어와도 session_id가 하나만 생성되게 한다.
        boolean firstRequest = contentRedisRepository.setIdempotencyKeyIfAbsent(userId, requestId, sessionId, ttl);

        if (!firstRequest) {
            // 이미 처리 중이거나 완료된 요청은 FastAPI를 다시 호출하지 않고 Redis에 남은 세션 결과만 반환한다.
            String existingSessionId = contentRedisRepository.getSessionIdByRequestId(userId, requestId);
            if (existingSessionId == null || existingSessionId.isBlank()) {
                // 이미 요청된 것으로 Redis가 판단했는데, 그 요청에 매핑된 sessionId를 읽을 수가 없다.
                // e.g.) Redis key가 SET NX EX 판단 직후 만료되어, getSessionIdByRequestId()할 때 없어짐
                throw new BusinessException(ErrorCode.AI_SERVER_FAILED);
            }
            ContentRedisResult existingResult = contentRedisRepository.getContentResult(existingSessionId);
            // 기존 결과가 아직 guide_text/caption 없이 STARTED라면 프론트는 처리 중 화면을 유지할 수 있다.
            // 결과가 있으면 동일 request_id 재요청에도 같은 session_id와 같은 텍스트 결과를 받는다.
            return new ChatResponse(
                    existingSessionId,
                    existingResult.status(),
                    existingResult.guideText(),
                    existingResult.caption()
            );
        }

        // Spring은 keyword/draft/photo/video 생성에 관여하지 않고, 세션 시작 상태와 최종 발화만 초기화한다.
        contentRedisRepository.createStartedContent(sessionId, request.utterance());

        StoreContext storeContext = getStoreContext(userId);
        AiProcessUtteranceResponse aiResponse = aiContentClient.processUtterance(new AiProcessUtteranceRequest(
                sessionId,
                storeContext.storeId(),
                request.utterance(),
                storeContext.ownerPersona(),
                LocalDate.now().toString(),
                // 날씨 Open API 연동 전까지는 새 FastAPI 계약의 weather 구조만 유지하고 모든 필드를 null로 보낸다.
                // TODO: 날씨 Open API 완료 후 실제 temperature/precipitation/cloud_cover 등으로 채운다.
                AiWeatherRequest.empty()
        ));

        ContentStatus status = parseAiStatus(aiResponse.status());
        // FastAPI도 Redis를 갱신할 수 있지만, Spring 응답과 재요청 조회를 위해 텍스트 생성 결과를 한 번 더 반영한다.
        // Redis Repository 내부에서 FastAPI가 먼저 저장한 텍스트 필드는 덮지 않도록 방어한다.
        contentRedisRepository.updateTextGeneratedResult(
                sessionId,
                aiResponse.guideText(),
                aiResponse.caption(),
                status
        );

        return new ChatResponse(sessionId, status, aiResponse.guideText(), aiResponse.caption());
    }

    @Transactional(readOnly = true)
    public ContentImageUrlsResponseDto getContentImages(Long contentId) {
        Content content = getContentWithRelations(contentId);

        return new ContentImageUrlsResponseDto(
                content.getImages().stream()
                        .map(ContentImage::getS3Key)
                        .toList()
        );
    }

    @Transactional
    public ContentImageDeleteResponseDto deleteContentImage(Long contentId, UUID imageId) {
        // 현재 엔티티에는 soft delete 플래그가 없어 실제 삭제로 처리한다.
        findContentById(contentId);

        ContentImage contentImage = contentImageRepository.findByIdAndContent_Id(imageId, contentId)
                .orElseThrow(() -> new BusinessException(ErrorCode.CONTENT_IMAGE_NOT_FOUND));

        contentImageRepository.delete(contentImage);

        long remainingImages = contentImageRepository.countByContent_Id(contentId);
        return new ContentImageDeleteResponseDto(true, remainingImages);
    }

    @Transactional(readOnly = true)
    public ContentResponseDto getContent(Long contentId) {
        return ContentResponseDto.from(getContentWithRelations(contentId));
    }

    @Transactional
    public ContentEditResponseDto updateContent(Long contentId, ContentEditRequestDto requestDto) {
        Content content = findContentById(contentId);

        // 현재 스키마에는 status/hashtags/updatedAt이 없어 caption만 수정한다.
        content.updateCaption(requestDto.caption());

        return ContentEditResponseDto.from(content);
    }

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

    private StoreContext getStoreContext(String userId) {
        // FastAPI caption 생성에 필요한 매장 식별자와 점주 성향값을 조회한다.
        // 현재 인증 userId가 UUID 문자열이라는 전제에서 stores.user_id와 매칭한다.
        // 인증/온보딩 데이터가 아직 없거나 임시 유저라면 기본값으로 API 계약만 유지한다.
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
