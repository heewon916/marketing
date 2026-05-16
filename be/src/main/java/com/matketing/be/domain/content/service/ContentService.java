package com.matketing.be.domain.content.service;

import com.matketing.be.domain.content.client.AiContentClient;
import com.matketing.be.domain.content.client.ClovaSttClient;
import com.matketing.be.domain.content.client.ClovaTtsClient;
import com.matketing.be.domain.content.client.InstagramPublishClient;
import com.matketing.be.domain.content.client.S3VideoClient;
import com.matketing.be.domain.content.config.ContentS3Properties;
import com.matketing.be.domain.content.config.ContentProperties;
import com.matketing.be.domain.content.dto.AiExtractFramesRequest;
import com.matketing.be.domain.content.dto.AiExtractFramesResponse;
import com.matketing.be.domain.content.dto.AiFinalEditRequest;
import com.matketing.be.domain.content.dto.AiFinalEditResponse;
import com.matketing.be.domain.content.dto.AiProcessUtteranceRequest;
import com.matketing.be.domain.content.dto.AiProcessUtteranceResponse;
import com.matketing.be.domain.content.dto.AiWeatherRequest;
import com.matketing.be.domain.content.dto.ChatRequest;
import com.matketing.be.domain.content.dto.ChatResponse;
import com.matketing.be.domain.content.dto.ContentDraftResponseDto;
import com.matketing.be.domain.content.dto.ContentRequest;
import com.matketing.be.domain.content.dto.ContentResponse;
import com.matketing.be.domain.content.dto.ContentEditRequestDto;
import com.matketing.be.domain.content.dto.ContentEditResponseDto;
import com.matketing.be.domain.content.dto.ContentImageDeleteResponseDto;
import com.matketing.be.domain.content.dto.ContentImageUrlsResponseDto;
import com.matketing.be.domain.content.dto.ContentPublishResponseDto;
import com.matketing.be.domain.content.dto.ContentPublishStatusResponseDto;
import com.matketing.be.domain.content.dto.ContentRedisResult;
import com.matketing.be.domain.content.dto.ContentVideoResponseDto;
import com.matketing.be.domain.content.dto.LlamaIntentResponse;
import com.matketing.be.domain.content.dto.SttResponse;
import com.matketing.be.domain.content.entity.Content;
import com.matketing.be.domain.content.enums.ContentStatus;
import com.matketing.be.domain.content.redis.ContentRedisRepository;
import com.matketing.be.domain.content.redis.ContentRedisRepository.ContentRedisSession;
import com.matketing.be.domain.content.repository.ContentRepository;
import com.matketing.be.domain.store.entity.Store;
import com.matketing.be.domain.store.repository.StoreRepository;
import com.matketing.be.domain.user.entity.User;
import com.matketing.be.domain.user.repository.UserRepository;
import com.matketing.be.global.auth.jwt.AuthUser;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@Service
@RequiredArgsConstructor
public class ContentService {

    private static final Set<String> ALLOWED_AUDIO_CONTENT_TYPES = Set.of(
            "audio/wav",
            "audio/x-wav",
            "audio/mpeg",
            "audio/mp3",
            "audio/mp4",
            "audio/x-m4a",
            "audio/m4a",
            "audio/aac",
            "audio/ac3",
            "audio/ogg",
            "audio/flac",
            "audio/webm"
    );
    private static final Set<String> ALLOWED_AUDIO_EXTENSIONS = Set.of(
            "wav",
            "mp3",
            "m4a",
            "mp4",
            "aac",
            "ac3",
            "ogg",
            "flac",
            "webm"
    );
    private static final String TEXT_RECOGNIZED = "TEXT_RECOGNIZED";

    private final ContentRepository contentRepository;
    private final ClovaSttClient clovaSttClient;
    private final AiContentClient aiContentClient;
    private final S3VideoClient s3VideoClient;
    private final ContentRedisRepository contentRedisRepository;
    private final ContentProperties contentProperties;
    private final ContentS3Properties contentS3Properties;
    private final InstagramPublishClient instagramPublishClient;
    private final UserRepository userRepository;
    private final StoreRepository storeRepository;
    private final WeatherContextProvider weatherService;
    private final ClovaTtsClient clovaTtsClient;
    private final ChatClient chatClient;


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
     * [Clova TTS]
     * 프론트엔드에서 전달받은 텍스트를 기반으로 네이버 Clova API에 오디오 생성을 요청한다.
     */
    public byte[] generateAudio(String text) {
        if (text == null || text.isBlank()) {
            throw new IllegalArgumentException("텍스트가 비어 있습니다.");
        }
        return clovaTtsClient.synthesize(text);
    }


    /**
     * [게시물 생성 로직] api/v1/contents/{sessionId}/caption 핵심 비즈니스 로직
     * - 기존 ChatRequest를 신규 ContentRequest로 변환해 실제 처리 메서드로 위임한다.
     * - 기존 프론트/테스트 코드와의 호환성을 유지하기 위한 어댑터 역할이다.
     * @param request request_id, 최종 utterance
     * @param userId 인증 사용자 식별자
     * @return AI 캡션 생성 응답
     */
    public ChatResponse createTextContent(ChatRequest request) {
        return createTextContent(new ContentRequest(request.requestId(), null, request.utterance()));
    }

    /**
     * [게시물 캡션 요청 분기]
     * - request_id가 있으면 기존 캡션 생성 플로우를 실행한다.
     * - request_id가 없으면 FastAPI 호출 없이 AI 게시글 생성에 필요한 참고 JSON만 생성한다.
     * @param request store_id, request_id(선택), utterance
     * @param userId 인증 사용자 식별자
     * @return ChatResponse 또는 ContentResponse
     */
    public Object createCaption(ContentRequest request) {
        // request_id는 멱등성 키이므로, 값이 있는 요청은 기존 캡션 생성 트리거로 판단한다.
        if (request.requestId() != null && !request.requestId().isBlank()) {
            return createTextContent(request);
        }
        return createCaptionContext(request);
    }

    /**
     * [AI 게시글 생성 참고정보 생성]
     * - store_id 또는 인증 사용자 기준으로 매장을 조회한다.
     * - 매장의 owner_persona, 좌표, 주소를 사용해 날씨/대기질/특보 정보를 조합한다.
     * - FastAPI를 호출하지 않고, /ai/sessions/{session_id}/process-utterance 요청 바디와 같은 참고 JSON을 반환한다.
     * @param request store_id, utterance
     * @param userId 인증 사용자 식별자
     * @return store, utterance, persona, date, weather가 포함된 참고정보 응답
     */
    public ContentResponse createCaptionContext(ContentRequest request) {
        // utterance는 AI 게시글 생성의 핵심 입력이므로 빈 값이면 즉시 차단한다.
        if (request.utterance() == null || request.utterance().isBlank()) {
            throw new BusinessException(ErrorCode.EMPTY_UTTERANCE);
        }

        // store_id가 있으면 해당 매장을 우선 사용하고, 없으면 인증 사용자에게 연결된 매장을 사용한다.
        Store store = getStore(request.storeId(), currentUserId());
        String ownerPersona = ownerPersona(store);
        String date = LocalDate.now().toString();

        // WeatherService 내부에서 Redis 캐시 조회 후, miss일 때만 외부 날씨/대기질 API를 호출한다.
        AiWeatherRequest weather = weatherService.getWeatherContext(store, LocalDateTime.now());

        return new ContentResponse(
                store.getId().toString(),
                request.utterance(),
                ownerPersona,
                date,
                weather
        );
    }

    /**
     * [AI 캡션 생성 실행]
     * - request_id 기반 Redis 멱등성 키를 생성한다.
     * - 최초 요청이면 store/weather 컨텍스트를 만든 뒤 FastAPI process-utterance를 호출한다.
     * - 중복 요청이면 FastAPI를 재호출하지 않고 Redis에 저장된 기존 처리 결과를 반환한다.
     * @param request store_id(선택), request_id, utterance
     * @param userId 인증 사용자 식별자
     * @return FastAPI 캡션 생성 결과
     */
    public ChatResponse createTextContent(ContentRequest request) {
        // 1. utterance empty 검사
        if (request.utterance() == null || request.utterance().isBlank()) {
            throw new BusinessException(ErrorCode.EMPTY_UTTERANCE);
        }
        if (request.requestId() == null || request.requestId().isBlank()) {
            throw new BusinessException(ErrorCode.INVALID_REQUEST);
        }
        parseUuid(request.requestId()).orElseThrow(() -> new BusinessException(ErrorCode.INVALID_REQUEST));

        // 2. request_id + session_id 기준으로 Redis 멱등성 key 생성
        String userId = currentUserId();
        String requestId = request.requestId();

        // [NEW] Llama 의도 파악 로직 추가
        LlamaIntentResponse llamaResp = chatClient.prompt()
                .user(request.utterance())
                .system("당신은 카페 사장님을 돕는 친절한 AI 어시스턴트입니다. 사용자의 입력이 인스타그램 게시물(피드) 생성을 요청하거나 의도하는 것이라면 isCreatePost를 true로 설정하세요. 만약 단순한 일상 대화나 감정 표현이라면 isCreatePost를 false로 설정하고, 카페 사장님과 대화하듯 다정하고 친근한 답변을 reply에 작성하세요.")
                .call()
                .entity(LlamaIntentResponse.class);

        if (!llamaResp.isCreatePost()) {
            return new ChatResponse(
                    null,
                    ContentStatus.GENERAL_CHAT,
                    "",
                    llamaResp.reply()
            );
        }

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

        // 4. store 정보를 들고 온다
        Store store = getStore(request.storeId(), userId);
        String ownerPersona = ownerPersona(store);

        // 5. 최초 요청일 경우: Redis에 contents:{sessionId} 최소 필드를 초기화한다.
        contentRedisRepository.createStartedContent(sessionId, store.getId().toString(), request.utterance());

        // 6. 매장 좌표/주소 기반 날씨 참고정보를 생성한다. 외부 API 실패 시 가능한 필드는 null로 채워진다.
        AiWeatherRequest weather = weatherService.getWeatherContext(store, LocalDateTime.now());

        // 7. ai/sessions/{session_id}/process_utterance API를 호출하는 곳이다.
        // FastAPI가 게시글 생성에 사용할 store/persona/date/weather 컨텍스트를 request body에 포함한다.
        AiProcessUtteranceResponse aiResponse = aiContentClient.processUtterance(new AiProcessUtteranceRequest(
                sessionId,
                store.getId().toString(),
                request.utterance(),
                ownerPersona,
                LocalDate.now().toString(),
                weather
        ));

        // 8. AI서버의 응답을 파싱해서 프론트에 응답함과 동시에, putIfAbsent패턴으로 Redis를 갱신한다.
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
     * [게시물 이미지 조회] /api/v1/contents/{sessionId}/images 핵심 비즈니스 로직
     * @param sessionId
     * @return
     */
    @Transactional(readOnly = true)
    public ContentImageUrlsResponseDto getContentImages(UUID sessionId) {
        return new ContentImageUrlsResponseDto(
                sessionId,
                contentRedisRepository.getPhotoUrls(sessionId.toString()).stream()
                        .map(photo -> new ContentImageUrlsResponseDto.ImageUrlItem(photo.field(), photo.url()))
                        .toList()
        );
    }

    /**
     * [게시물 이미지 삭제] /api/v1/contents/{sessionId}/images/delete 핵심 비즈니스 로직
     * @param sessionId
     * @param imageUrl
     * @return
     */
    @Transactional
    public ContentImageDeleteResponseDto deleteContentImage(UUID sessionId, String deletedImageKey) {
        if (deletedImageKey == null || deletedImageKey.isBlank()) {
            throw new BusinessException(ErrorCode.INVALID_REQUEST);
        }

        boolean deleted = contentRedisRepository.deletePhotoByField(sessionId.toString(), deletedImageKey);
        if (!deleted) {
            throw new BusinessException(ErrorCode.CONTENT_IMAGE_NOT_FOUND);
        }

        long remainingImages = contentRedisRepository.getPhotoUrlValues(sessionId.toString()).size();
        return new ContentImageDeleteResponseDto(true, remainingImages);
    }

    /**
     * [게시물 내용 조회] /api/v1/contents/{sessionId} 핵심 비즈니스 로직
     * @param sessionId
     * @return
     */
    @Transactional(readOnly = true)
    public ContentDraftResponseDto getContent(UUID sessionId) {
        ContentRedisSession session = getRedisSessionOrThrow(sessionId);
        AuthUser user = currentAuthUser();
        List<ContentDraftResponseDto.ImageItem> images = contentRedisRepository.getPhotoUrls(sessionId.toString()).stream()
                .map(photo -> new ContentDraftResponseDto.ImageItem(photo.field(), photo.url(), photo.displayOrder()))
                .toList();
        return new ContentDraftResponseDto(
                sessionId,
                normalizeDraftStatus(session.status()),
                session.caption(),
                images,
                user.getInstagramUsername(),
                user.getProfileImageUrl()
        );
    }

    /**
     * [게시물 텍스트 갱신] /api/v1/contents/{sessionId}/edit 핵심 비즈니스 로직
     * @param sessionId
     * @param requestDto 캡션만 수정 가능하다.
     * @return 수정된
     */
    @Transactional
    public ContentEditResponseDto updateContent(UUID sessionId, ContentEditRequestDto requestDto) {
        if (requestDto.caption() == null || requestDto.caption().isBlank()) {
            throw new BusinessException(ErrorCode.INVALID_REQUEST);
        }

        OffsetDateTime updatedAt = OffsetDateTime.now();
        boolean updated = contentRedisRepository.updateCaption(sessionId.toString(), requestDto.caption(), updatedAt);
        if (!updated) {
            throw new BusinessException(ErrorCode.CONTENT_NOT_FOUND);
        }

        return new ContentEditResponseDto(sessionId, requestDto.caption(), updatedAt);
    }

    public ContentPublishResponseDto publishContent(UUID sessionId) {
        ContentRedisSession session = getRedisSessionOrThrow(sessionId);
        if (session.contentId() != null && !session.contentId().isBlank()) {
            return new ContentPublishResponseDto(
                    session.contentId(),
                    "completed",
                    "이미 발행된 게시물입니다"
            );
        }
        if (session.publishId() != null && !session.publishId().isBlank()
                && session.instagramContainerId() != null && !session.instagramContainerId().isBlank()
        ) {
            return new ContentPublishResponseDto(
                    session.publishId(),
                    safePublishProgress(session.publishProgress()),
                    "발행이 진행 중입니다"
            );
        }
        if (session.caption() == null || session.caption().isBlank()) {
            throw new BusinessException(ErrorCode.INVALID_REQUEST);
        }

        List<String> imageUrls = session.photos().stream()
                .map(this::toPublicMediaUrl)
                .toList();

        if (imageUrls.isEmpty()) {
            if (session.video() != null && !session.video().isBlank()) {
                throw new BusinessException(ErrorCode.INVALID_REQUEST, "현재는 이미지 기반 Instagram 발행만 지원합니다.");
            }
            throw new BusinessException(ErrorCode.INSTAGRAM_MEDIA_REQUIRED);
        }

        if (imageUrls.size() > 10) {
            throw new BusinessException(ErrorCode.INVALID_REQUEST, "최대 10장의 이미지만 발행할 수 있습니다.");
        }

        User user = currentUser();
        Store store = storeRepository.findFirstByUserId(user.getId())
                .orElseThrow(() -> new BusinessException(ErrorCode.STORE_NOT_FOUND));

        validateInstagramToken(user);

        log.info("[Publish] Store resolved from DB. userId={}, storeId={}", user.getId(), store.getId());

        log.info("[Publish] Starting publish process. sessionId={}, userId={}, igUserId={}, photoCount={}, hasVideo={}",
                sessionId, user.getId(), user.getInstagramUserId(), imageUrls.size(), session.video() != null && !session.video().isBlank());

        if (session.video() != null && !session.video().isBlank()) {
            log.info("[Publish] Video exists in session but is ignored for Instagram publishing. sessionId={}", sessionId);
        }

        String publishId = UUID.randomUUID().toString();
        boolean queued = contentRedisRepository.queuePublish(sessionId.toString(), publishId);
        if (!queued) {
            throw new BusinessException(ErrorCode.CONTENT_NOT_FOUND);
        }
        try {
            String containerId = createInstagramContainer(user, session.caption(), imageUrls);
            contentRedisRepository.markPublishContainerCreated(sessionId.toString(), containerId);
        } catch (BusinessException exception) {
            contentRedisRepository.failPublish(sessionId.toString(), exception.getMessage());
            throw exception;
        }
        return new ContentPublishResponseDto(publishId, "queued", "발행이 시작되었습니다");
    }

    /**
     * 게시물 발행 상태 조회 API.
     * Side Effect Warning: 이 메서드는 단순 상태 조회뿐만 아니라, 컨테이너 상태가 FINISHED일 때 media_publish와 DB 저장을 수행합니다.
     * 따라서 멱등성(Idempotency)을 보장하기 위해 Redis Lock과 상태(status/instagram_media_id) 체크가 포함되어 있습니다.
     */
    @Transactional
    public ContentPublishStatusResponseDto getPublishStatus(UUID sessionId) {
        ContentRedisSession session = getRedisSessionOrThrow(sessionId);
        if (session.contentId() != null && !session.contentId().isBlank()) {
            return new ContentPublishStatusResponseDto(
                    session.contentId(),
                    "completed",
                    session.instagramMediaId(),
                    session.instagramPermalink()
            );
        }

        // media_publish는 성공했으나 이전 호출에서 DB 저장이 실패했던 경우 복구를 시도
        if (session.instagramMediaId() != null && !session.instagramMediaId().isBlank()) {
            User user = currentUser();
            Store store = storeRepository.findFirstByUserId(user.getId())
                    .orElseThrow(() -> new BusinessException(ErrorCode.STORE_NOT_FOUND));
            return completePublishAndSave(sessionId, session, user, session.instagramMediaId(), store);
        }

        if (session.publishId() == null || session.publishId().isBlank()) {
            return new ContentPublishStatusResponseDto(null, "not_started", null, null);
        }

        if (ContentStatus.PUBLISH_FAILED.name().equals(session.status()) || "failed".equalsIgnoreCase(session.publishProgress())) {
            return new ContentPublishStatusResponseDto(null, "failed", null, null);
        }

        if (session.instagramContainerId() == null || session.instagramContainerId().isBlank()) {
            return new ContentPublishStatusResponseDto(null, safePublishProgress(session.publishProgress()), null, null);
        }

        User user = currentUser();
        Store store = storeRepository.findFirstByUserId(user.getId())
                .orElseThrow(() -> new BusinessException(ErrorCode.STORE_NOT_FOUND));

        validateInstagramToken(user);

        log.info("[PublishStatus] Store resolved from DB. sessionId={}, userId={}, storeId={}", sessionId, user.getId(), store.getId());

        try {
            String containerStatus = instagramPublishClient.getContainerStatus(user.getAccessToken(), session.instagramContainerId());
            if ("IN_PROGRESS".equalsIgnoreCase(containerStatus)) {
                contentRedisRepository.markPublishInProgress(sessionId.toString());
                return new ContentPublishStatusResponseDto(null, "uploading", null, null);
            }
            if (!"FINISHED".equalsIgnoreCase(containerStatus)) {
                contentRedisRepository.failPublish(sessionId.toString(), "Instagram container status: " + containerStatus);
                return new ContentPublishStatusResponseDto(null, "failed", null, null);
            }

            if (!contentRedisRepository.acquirePublishLock(sessionId.toString())) {
                log.info("[Publish] Concurrent polling detected. Locked by another request. sessionId={}", sessionId);
                return new ContentPublishStatusResponseDto(null, "uploading", null, null);
            }

            String instagramMediaId = instagramPublishClient.publishContainer(
                    user.getInstagramUserId(),
                    user.getAccessToken(),
                    session.instagramContainerId()
            );

            // media_publish 성공 직후 Redis에 id를 저장하여 동시성 및 재시도 상황 대비
            contentRedisRepository.saveInstagramMediaId(sessionId.toString(), instagramMediaId);

            return completePublishAndSave(sessionId, session, user, instagramMediaId, store);

        } catch (BusinessException exception) {
            contentRedisRepository.failPublish(sessionId.toString(), exception.getMessage());
            return new ContentPublishStatusResponseDto(null, "failed", null, null);
        }
    }

    private ContentPublishStatusResponseDto completePublishAndSave(UUID sessionId, ContentRedisSession session, User user, String instagramMediaId, Store store) {
        String instagramPermalink;
        try {
            instagramPermalink = instagramPublishClient.getPermalink(user.getAccessToken(), instagramMediaId);

            Content content = Content.builder()
                    .storeId(store.getId())
                    .sessionId(sessionId)
                    .caption(session.caption())
                    .instagramMediaId(instagramMediaId)
                    .instagramPermalink(instagramPermalink)
                    .publishedAt(OffsetDateTime.now())
                    .isDeleted(false)
                    .createdAt(OffsetDateTime.now())
                    .build();
            content.replaceImages(session.photos());
            content.replaceVideoRecordings(session.video() == null || session.video().isBlank() ? List.of() : List.of(session.video()));
            Content saved = contentRepository.save(content);
            contentRedisRepository.completePublish(sessionId.toString(), saved.getId(), instagramMediaId, instagramPermalink);

            return new ContentPublishStatusResponseDto(
                    String.valueOf(saved.getId()),
                    "completed",
                    instagramMediaId,
                    instagramPermalink
            );
        } catch (Exception exception) {
            log.error("[Publish] Instagram publish succeeded but DB save failed. sessionId={}, mediaId={}", sessionId, instagramMediaId, exception);
            contentRedisRepository.failPublish(sessionId.toString(), "Instagram 게시는 성공했지만 서버 저장 실패");
            return new ContentPublishStatusResponseDto(null, "failed", null, null);
        }
    }

    public ContentVideoResponseDto processVideo(UUID sessionId, String storeId, MultipartFile videoFile) {
        try {
            validateVideoFile(videoFile);
            String videoKey = "/inputs/" + sessionId + "/draft.mp4";

            log.info("[VideoUpload] uploading original video to S3. key={}", videoKey);
            s3VideoClient.uploadVideo(videoKey, videoFile);
            log.info("[VideoUpload] S3 upload completed. key={}", videoKey);

            boolean videoSaved = contentRedisRepository.putVideo(sessionId.toString(), videoKey);
            if (!videoSaved) {
                log.error("[VideoUpload] failed at step=Redis putVideo, sessionId={}, storeId={}, reason=Redis save failed", sessionId, storeId);
                throw new BusinessException(ErrorCode.CONTENT_NOT_FOUND);
            }

            log.info("[VideoUpload] calling AI extract-frames. sessionId={}, videoKey={}", sessionId, videoKey);
            AiExtractFramesResponse extracted = null;
            try {
                extracted = aiContentClient.extractFrames(
                        new AiExtractFramesRequest(sessionId.toString(), videoKey)
                );
            } catch (Exception e) {
                log.error("[VideoUpload] failed at step=AI extractFrames, sessionId={}, storeId={}, reason={}", sessionId, storeId, e.getMessage());
                throw new BusinessException(ErrorCode.AI_SERVER_FAILED);
            }

            List<String> drafts = extracted != null && extracted.drafts() != null
                    ? extracted.drafts().stream()
                    .filter(draft -> draft != null && !draft.isBlank())
                    .toList()
                    : List.of();

            log.info("[VideoUpload] AI extract-frames response received. status={}, draftsCount={}",
                    extracted != null ? extracted.status() : "null", drafts.size());

            log.info("[VideoUpload] calling AI final-edit. sessionId={}", sessionId);
            AiFinalEditResponse edited = null;
            try {
                edited = aiContentClient.finalEdit(
                        new AiFinalEditRequest(sessionId.toString(), drafts)
                );
            } catch (Exception e) {
                log.error("[VideoUpload] failed at step=AI finalEdit, sessionId={}, storeId={}, reason={}", sessionId, storeId, e.getMessage());
                throw new BusinessException(ErrorCode.AI_SERVER_FAILED);
            }

            List<String> results = edited != null && edited.results() != null ? edited.results() : List.of();
            String status = edited != null && edited.status() != null ? edited.status() : ContentStatus.PHOTO_EDITED.name();

            log.info("[VideoUpload] AI final-edit response received. status={}, resultsCount={}", status, results.size());

            contentRedisRepository.putAiVideoResults(sessionId.toString(), videoKey, status, drafts, results);

            List<ContentVideoResponseDto.ExtractedFrame> frames = results.stream()
                    .map(result -> new ContentVideoResponseDto.ExtractedFrame(UUID.randomUUID().toString(), result))
                    .toList();
            return new ContentVideoResponseDto(videoKey, frames);
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("[VideoUpload] failed at step=Unknown, sessionId={}, storeId={}, reason={}", sessionId, storeId, e.getMessage(), e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    //============================================
    // 여기서부터는 부가 로직이다.
    //============================================
    // STT에 전달할 수 있는 오디오 파일인지 사전 검증한다.
    // content-type을 우선 신뢰하되, 모바일/브라우저 환경에서 content-type이 빠질 수 있어 확장자를 보조 기준으로 허용한다.
    // 둘 다 허용 목록에 없거나 파일이 비어 있으면 INVALID_AUDIO_FILE로 통일한다.
    private void validateAudioFile(MultipartFile audioFile) {
        if (audioFile == null || audioFile.isEmpty()) {
            throw new BusinessException(ErrorCode.INVALID_AUDIO_FILE);
        }

        // 클라이언트/브라우저별 content-type 누락 가능성을 고려해 확장자를 보조 검증으로 허용한다.
        String contentType = normalizeContentType(audioFile.getContentType());
        if (contentType != null && ALLOWED_AUDIO_CONTENT_TYPES.contains(contentType)) {
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

    private String normalizeContentType(String contentType) {
        if (contentType == null || contentType.isBlank()) {
            return null;
        }
        return contentType.split(";", 2)[0].trim().toLowerCase(Locale.ROOT);
    }

    private void validateVideoFile(MultipartFile videoFile) {
        if (videoFile == null || videoFile.isEmpty()) {
            throw new BusinessException(ErrorCode.INVALID_REQUEST);
        }
    }

    /**
     * 캡션/참고정보 생성 시 store 정보 조회에 사용된다.
     * - 요청에 store_id가 있으면 해당 store를 우선 조회한다.
     * - store_id가 없거나 UUID가 아니면 인증 사용자 기준으로 1개의 store를 조회한다.
     * - 둘 다 실패하면 게시글 생성에 필요한 매장 컨텍스트가 없으므로 STORE_NOT_FOUND를 반환한다.
     * @param storeId 요청으로 전달된 매장 UUID
     * @param userId 인증 사용자 UUID
     * @return 게시글 생성에 사용할 Store
     */
    private Store getStore(String storeId, String userId) {
        Optional<Store> store = parseUuid(storeId)
                .flatMap(storeRepository::findById)
                .or(() -> parseUuid(userId).flatMap(storeRepository::findFirstByUserId));
        return store.orElseThrow(() -> new BusinessException(ErrorCode.STORE_NOT_FOUND));
    }

    /**
     * 매장 owner_persona를 반환한다.
     * - DB 값이 없을 때는 AI 서버 기본 기대값인 aesthetic을 사용한다.
     * @param store 매장 엔티티
     * @return owner_persona
     */
    private String ownerPersona(Store store) {
        String ownerPersona = store.getOwnerPersona() != null ? store.getOwnerPersona().name() : null;
        if (ownerPersona == null || ownerPersona.isBlank()) {
            ownerPersona = "aesthetic";
        }
        return ownerPersona;
    }

    /**
     * 문자열 UUID 파싱 헬퍼.
     * - store_id/user_id가 비어 있거나 UUID 형식이 아니면 Optional.empty()로 반환해 fallback 조회가 가능하게 한다.
     * @param value UUID 문자열
     * @return 파싱된 UUID
     */
    private Optional<UUID> parseUuid(String value) {
        if (value == null || value.isBlank()) {
            return Optional.empty();
        }
        try {
            return Optional.of(UUID.fromString(value));
        } catch (IllegalArgumentException exception) {
            return Optional.empty();
        }
    }

    private ContentRedisSession getRedisSessionOrThrow(UUID sessionId) {
        ContentRedisSession session = contentRedisRepository.getSession(sessionId.toString());
        if (session == null) {
            throw new BusinessException(ErrorCode.CONTENT_NOT_FOUND);
        }
        return session;
    }

    private String normalizeDraftStatus(String status) {
        if (status == null || status.isBlank()) {
            return "draft";
        }
        return status;
    }

    private AuthUser currentAuthUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !(authentication.getPrincipal() instanceof AuthUser authUser)) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED_USER);
        }
        return authUser;
    }

    private User currentUser() {
        return userRepository.findById(currentAuthUser().getId())
                .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
    }

    private String currentUserId() {
        return currentAuthUser().getId().toString();
    }

    private void validateInstagramToken(User user) {
        if (user.getAccessToken() == null || user.getAccessToken().isBlank()) {
            throw new BusinessException(ErrorCode.INSTAGRAM_TOKEN_REQUIRED);
        }
        if (user.getInstagramUserId() == null || user.getInstagramUserId().isBlank()) {
            throw new BusinessException(ErrorCode.INSTAGRAM_TOKEN_REQUIRED);
        }
        if (user.getTokenExpiresAt() != null && user.getTokenExpiresAt().isBefore(OffsetDateTime.now())) {
            throw new BusinessException(ErrorCode.INSTAGRAM_TOKEN_REQUIRED);
        }
    }

    private String createInstagramContainer(User user, String caption, List<String> imageUrls) {
        if (imageUrls.size() == 1) {
            return instagramPublishClient.createImageContainer(
                    user.getInstagramUserId(),
                    user.getAccessToken(),
                    imageUrls.getFirst(),
                    caption
            );
        }
        return instagramPublishClient.createCarouselContainer(
                user.getInstagramUserId(),
                user.getAccessToken(),
                imageUrls,
                caption
        );
    }

    private String toPublicMediaUrl(String mediaPath) {
        if (mediaPath == null || mediaPath.isBlank()) {
            throw new BusinessException(ErrorCode.INSTAGRAM_MEDIA_REQUIRED);
        }
        String trimmed = mediaPath.trim();
        if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
            return trimmed;
        }

        String baseUrl = contentS3Properties.publicBaseUrl();
        if (baseUrl == null || baseUrl.isBlank()) {
            throw new BusinessException(ErrorCode.INSTAGRAM_MEDIA_REQUIRED);
        }
        String normalizedBase = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        String normalizedPath = trimmed.startsWith("/") ? trimmed.substring(1) : trimmed;
        return normalizedBase + "/" + normalizedPath;
    }

    private String safePublishProgress(String progress) {
        return progress == null || progress.isBlank() ? "queued" : progress;
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

}
