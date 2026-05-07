package com.matketing.be.domain.content.redis;

import com.matketing.be.domain.content.dto.ContentRedisResult;
import com.matketing.be.domain.content.enums.ContentStatus;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class ContentRedisRepository {

    private static final String STATUS = "status";
    private static final String UTTERANCE = "utterance";
    private static final String GUIDE_TEXT = "guide_text";
    private static final String CAPTION = "caption";

    private final StringRedisTemplate redisTemplate;

    // request_id 멱등성 key를 최초 요청에서만 생성한다.
    // 성공하면 이 요청이 FastAPI 호출을 담당하고, 실패하면 이미 같은 사용자/request_id의 요청이 처리 중이거나 완료된 상태다.
    public boolean setIdempotencyKeyIfAbsent(String userId, String requestId, String sessionId, Duration ttl) {
        // setIfAbsent(key, value, ttl)는 Redis SET key value NX EX와 동일한 원자 연산으로 동작한다.
        Boolean result = redisTemplate.opsForValue()
                .setIfAbsent(idempotencyKey(userId, requestId), sessionId, ttl);
        return Boolean.TRUE.equals(result);
    }

    // 중복 요청에서 기존 request_id가 어떤 session_id에 묶였는지 조회한다.
    // TTL 만료, 외부 삭제, Redis 이상 상태에서는 null이 반환될 수 있어 Service에서 방어한다.
    public String getSessionIdByRequestId(String userId, String requestId) {
        return redisTemplate.opsForValue().get(idempotencyKey(userId, requestId));
    }


    /**
     * contents:{session_id} Hash의 최소 필드 생성
     * - 주의사항: Fast API와 공유하므로, status/utterance는 putIfAbsent 패턴으로 처리한다
     * @param sessionId
     * @param utterance
     */
    public void createStartedContent(String sessionId, String utterance) {
        String key = contentKey(sessionId);  // contents:{sessionId} 생성
        redisTemplate.opsForHash().putIfAbsent(key, STATUS, ContentStatus.STARTED.name());
        redisTemplate.opsForHash().putIfAbsent(key, UTTERANCE, utterance);
    }

    // 프론트 재요청 또는 중복 요청 응답에 필요한 텍스트 생성 결과만 조회한다.
    // keyword/draft/photo/video 등 FastAPI 상세 필드는 Spring 응답 대상이 아니므로 여기서 읽지 않는다.
    // Hash가 아직 없으면 idempotency key만 먼저 보이는 처리 중 구간으로 보고 STARTED를 반환한다.
    public ContentRedisResult getContentResult(String sessionId) {
        Map<Object, Object> entries = redisTemplate.opsForHash().entries(contentKey(sessionId));
        if (entries.isEmpty()) {
            // idempotency key는 있지만 Hash가 아직 보이지 않는 짧은 구간은 처리 중 상태로 응답한다.
            return new ContentRedisResult(sessionId, ContentStatus.STARTED, null, null);
        }

        ContentStatus status = ContentStatus.fromExternal((String) entries.get(STATUS));
        return new ContentRedisResult(
                sessionId,
                status,
                (String) entries.get(GUIDE_TEXT),
                (String) entries.get(CAPTION)
        );
    }

    // FastAPI 응답으로 받은 텍스트 생성 결과를 Redis에 보강한다.
    // guide_text/caption은 FastAPI가 먼저 저장했을 수 있으므로 없을 때만 채운다.
    // status는 STARTED에서 TEXT_GENERATED 이상으로 진행되어야 하므로 별도 진행도 비교 로직을 사용한다.
    public void updateTextGeneratedResult(String sessionId, String guideText, String caption, ContentStatus status) {
        // 주의: FastAPI가 먼저 저장한 텍스트 결과를 덮지 않는다.
        String key = contentKey(sessionId);

        updateStatusIfProgressed(key, status);

        if (guideText != null && !guideText.isBlank()) {
            redisTemplate.opsForHash().putIfAbsent(key, GUIDE_TEXT, guideText);
        }

        if (caption != null && !caption.isBlank()) {
            redisTemplate.opsForHash().putIfAbsent(key, CAPTION, caption);
        }
    }

    // Redis의 현재 status가 새 status보다 뒤 단계면 유지하고, 새 status가 더 진행된 단계일 때만 갱신한다.
    // 예를 들어 FastAPI가 이미 FRAME_EXTRACTED까지 진행했는데 Spring이 늦게 TEXT_GENERATED를 쓰면 상태가 역행하므로 막는다.
    // 현재 비교는 enum 선언 순서에 의존하므로 상태 추가/순서 변경 시 이 메서드도 함께 검토해야 한다.
    private void updateStatusIfProgressed(String key, ContentStatus newStatus) {
        Object currentValue = redisTemplate.opsForHash().get(key, STATUS);

        if (currentValue == null) {
            redisTemplate.opsForHash().put(key, STATUS, newStatus.name());
            return;
        }

        ContentStatus currentStatus = ContentStatus.fromExternal((String) currentValue);

        if (newStatus.ordinal() > currentStatus.ordinal()) {
            redisTemplate.opsForHash().put(key, STATUS, newStatus.name());
        }
    }

    private String idempotencyKey(String userId, String requestId) {
        return "idempotency:contents:chat:" + userId + ":" + requestId;
    }

    private String contentKey(String sessionId) {
        return "contents:" + sessionId;
    }
}
