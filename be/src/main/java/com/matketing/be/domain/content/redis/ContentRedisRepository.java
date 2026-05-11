package com.matketing.be.domain.content.redis;

import com.matketing.be.domain.content.dto.ContentRedisResult;
import com.matketing.be.domain.content.enums.ContentStatus;
import java.time.OffsetDateTime;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class ContentRedisRepository {

    private static final String STATUS = "status";
    private static final String UTTERANCE = "utterance";
    private static final String STORE_ID = "store_id";
    private static final String GUIDE_TEXT = "guide_text";
    private static final String CAPTION = "caption";
    private static final String VIDEO = "video";
    private static final String UPDATED_AT = "updated_at";
    private static final String PUBLISH_ID = "publish_id";
    private static final String PUBLISH_PROGRESS = "publish_progress";
    private static final String CONTENT_ID = "content_id";
    private static final String INSTAGRAM_MEDIA_ID = "instagram_media_id";
    private static final String INSTAGRAM_PERMALINK = "instagram_permalink";
    private static final String DRAFT_PREFIX = "draft:";
    private static final String PHOTO_PREFIX = "photo:";

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
    public void createStartedContent(String sessionId, String storeId, String utterance) {
        String key = contentKey(sessionId);  // contents:{sessionId} 생성
        redisTemplate.opsForHash().putIfAbsent(key, STATUS, ContentStatus.STARTED.name());
        redisTemplate.opsForHash().putIfAbsent(key, STORE_ID, storeId);
        redisTemplate.opsForHash().putIfAbsent(key, UTTERANCE, utterance);
    }

    public void createStartedContent(String sessionId, String utterance) {
        createStartedContent(sessionId, null, utterance);
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

    public List<RedisImageValue> getPhotoUrls(String sessionId) {
        return prefixedValues(sessionId, PHOTO_PREFIX).entrySet().stream()
                .map(entry -> new RedisImageValue(entry.getKey(), entry.getValue()))
                .toList();
    }

    public List<String> getPhotoUrlValues(String sessionId) {
        return getPhotoUrls(sessionId).stream()
                .map(RedisImageValue::url)
                .toList();
    }

    public List<String> getVideoKeys(String sessionId) {
        String video = getStringField(sessionId, VIDEO);
        if (video == null || video.isBlank()) {
            return List.of();
        }
        return List.of(video);
    }

    public boolean deletePhotoByField(String sessionId, String photoField) {
        String key = contentKey(sessionId);
        if (photoField == null || !isPhotoField(photoField)) {
            return false;
        }
        return redisTemplate.opsForHash().delete(key, photoField) > 0;
    }

    public boolean putVideo(String sessionId, String videoKey) {
        String key = contentKey(sessionId);
        if (redisTemplate.opsForHash().entries(key).isEmpty()) {
            return false;
        }
        redisTemplate.opsForHash().put(key, VIDEO, videoKey);
        return true;
    }

    public boolean putAiVideoResults(String sessionId, String videoKey, String status, List<String> drafts, List<String> photos) {
        String key = contentKey(sessionId);
        if (redisTemplate.opsForHash().entries(key).isEmpty()) {
            return false;
        }

        Map<String, String> mapping = new LinkedHashMap<>();
        mapping.put(VIDEO, videoKey);
        mapping.put(STATUS, status);
        redisTemplate.opsForHash().putAll(key, mapping);
        replacePrefixedFields(key, DRAFT_PREFIX, drafts);
        replacePrefixedFields(key, PHOTO_PREFIX, photos);
        return true;
    }

    public boolean updateCaption(String sessionId, String caption, OffsetDateTime updatedAt) {
        String key = contentKey(sessionId);
        if (redisTemplate.opsForHash().entries(key).isEmpty()) {
            return false;
        }

        redisTemplate.opsForHash().put(key, CAPTION, caption);
        redisTemplate.opsForHash().put(key, UPDATED_AT, updatedAt.toString());
        return true;
    }

    public boolean queuePublish(String sessionId, String publishId) {
        String key = contentKey(sessionId);
        if (redisTemplate.opsForHash().entries(key).isEmpty()) {
            return false;
        }
        redisTemplate.opsForHash().put(key, PUBLISH_ID, publishId);
        redisTemplate.opsForHash().put(key, PUBLISH_PROGRESS, "queued");
        return true;
    }

    public void completePublish(String sessionId, Long contentId, String instagramMediaId, String instagramPermalink) {
        String key = contentKey(sessionId);
        redisTemplate.opsForHash().put(key, CONTENT_ID, String.valueOf(contentId));
        redisTemplate.opsForHash().put(key, PUBLISH_PROGRESS, "completed");
        redisTemplate.opsForHash().put(key, INSTAGRAM_MEDIA_ID, instagramMediaId);
        redisTemplate.opsForHash().put(key, INSTAGRAM_PERMALINK, instagramPermalink);
        redisTemplate.opsForHash().put(key, STATUS, ContentStatus.COMPLETED.name());
    }

    public ContentRedisSession getSession(String sessionId) {
        Map<Object, Object> entries = redisTemplate.opsForHash().entries(contentKey(sessionId));
        if (entries.isEmpty()) {
            return null;
        }
        return new ContentRedisSession(
                sessionId,
                stringValue(entries.get(STORE_ID)),
                stringValue(entries.get(STATUS)),
                stringValue(entries.get(CAPTION)),
                stringValue(entries.get(VIDEO)),
                stringValue(entries.get(PUBLISH_ID)),
                stringValue(entries.get(PUBLISH_PROGRESS)),
                stringValue(entries.get(CONTENT_ID)),
                stringValue(entries.get(INSTAGRAM_MEDIA_ID)),
                stringValue(entries.get(INSTAGRAM_PERMALINK)),
                new ArrayList<>(prefixedValues(entries, PHOTO_PREFIX).values()),
                getPrefixedValues(entries, DRAFT_PREFIX)
        );
    }

    public String getStringField(String sessionId, String field) {
        Object value = redisTemplate.opsForHash().get(contentKey(sessionId), field);
        return value instanceof String stringValue ? stringValue : null;
    }

    private LinkedHashMap<String, String> prefixedValues(String sessionId, String prefix) {
        return prefixedValues(redisTemplate.opsForHash().entries(contentKey(sessionId)), prefix);
    }

    private LinkedHashMap<String, String> prefixedValues(Map<Object, Object> entries, String prefix) {
        LinkedHashMap<String, String> values = new LinkedHashMap<>();
        entries.entrySet().stream()
                .filter(entry -> isPrefixedField(entry.getKey(), prefix))
                .sorted(Comparator.comparingInt(entry -> prefixedIndex(entry.getKey(), prefix)))
                .forEach(entry -> values.put((String) entry.getKey(), stringValue(entry.getValue())));
        return values;
    }

    private List<String> getPrefixedValues(Map<Object, Object> entries, String prefix) {
        return prefixedValues(entries, prefix).values().stream()
                .filter(value -> value != null && !value.isBlank())
                .toList();
    }

    private void replacePrefixedFields(String key, String prefix, List<String> values) {
        Object[] oldFields = redisTemplate.opsForHash().entries(key).keySet().stream()
                .filter(field -> isPrefixedField(field, prefix))
                .toArray();
        if (oldFields.length > 0) {
            redisTemplate.opsForHash().delete(key, oldFields);
        }
        if (values == null) {
            return;
        }
        for (int index = 0; index < values.size(); index++) {
            redisTemplate.opsForHash().put(key, prefix + (index + 1), values.get(index));
        }
    }

    public boolean deletePhotoByUrl(String sessionId, String photoUrl) {
        String key = contentKey(sessionId);
        Object[] fieldsToDelete = redisTemplate.opsForHash().entries(key).entrySet().stream()
                .filter(entry -> isPhotoField(entry.getKey()))
                .filter(entry -> photoUrl.equals(entry.getValue()))
                .map(Map.Entry::getKey)
                .toArray();

        if (fieldsToDelete.length == 0) {
            return false;
        }

        redisTemplate.opsForHash().delete(key, fieldsToDelete);
        return true;
    }

    public boolean updateCaption(String sessionId, String caption) {
        return updateCaption(sessionId, caption, OffsetDateTime.now());
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

    private boolean isPhotoField(Object field) {
        return isPrefixedField(field, PHOTO_PREFIX);
    }

    private boolean isPrefixedField(Object field, String prefix) {
        return field instanceof String fieldName && fieldName.startsWith(prefix);
    }

    private int prefixedIndex(Object field, String prefix) {
        if (!(field instanceof String fieldName)) {
            return Integer.MAX_VALUE;
        }

        String suffix = fieldName.substring(prefix.length()).replace("{", "").replace("}", "");
        try {
            return Integer.parseInt(suffix);
        } catch (NumberFormatException exception) {
            return Integer.MAX_VALUE;
        }
    }

    private String stringValue(Object value) {
        return value instanceof String stringValue ? stringValue : null;
    }

    public record RedisImageValue(String field, String url) {
        public int displayOrder() {
            String suffix = field.substring(PHOTO_PREFIX.length()).replace("{", "").replace("}", "");
            try {
                return Integer.parseInt(suffix);
            } catch (NumberFormatException exception) {
                return 0;
            }
        }
    }

    public record ContentRedisSession(
            String sessionId,
            String storeId,
            String status,
            String caption,
            String video,
            String publishId,
            String publishProgress,
            String contentId,
            String instagramMediaId,
            String instagramPermalink,
            List<String> photos,
            List<String> drafts
    ) {
    }
}
