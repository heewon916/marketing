package com.matketing.be.domain.content.client;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;

@Component
@Slf4j
public class InstagramPublishClient {

    private final RestClient restClient;
    private final RestTemplate restTemplate;
    private final String apiVersion;
    private final ObjectMapper objectMapper;

    public InstagramPublishClient(
            RestClient.Builder builder,
            org.springframework.boot.web.client.RestTemplateBuilder restTemplateBuilder,
            @Value("${instagram.publish.base-url:https://graph.instagram.com}") String baseUrl,
            @Value("${instagram.graph-api.version:v25.0}") String apiVersion,
            ObjectMapper objectMapper
    ) {
        this.restClient = builder.baseUrl(baseUrl).build();
        this.restTemplate = restTemplateBuilder.build();
        this.apiVersion = apiVersion.startsWith("/") ? apiVersion : "/" + apiVersion;
        this.objectMapper = objectMapper;
    }

    public void validateCloudFrontUrl(String imageUrl) {
        try {
            ResponseEntity<Void> response = restTemplate.exchange(imageUrl, HttpMethod.HEAD, null, Void.class);
            MediaType contentType = response.getHeaders().getContentType();
            
            if (contentType == null || (!contentType.includes(MediaType.IMAGE_JPEG) && !contentType.includes(MediaType.IMAGE_PNG))) {
                log.error("[Validate] Image URL validation failed. Content-Type is {}", contentType);
                throw new BusinessException(ErrorCode.VALIDATION_ERROR);
            }
        } catch (BusinessException e) {
            throw e;
        } catch (Exception ex) {
            log.warn("[Validate] HEAD request failed for url={}, trying GET fallback", imageUrl);
            try {
                ResponseEntity<byte[]> getResponse = restTemplate.exchange(imageUrl, HttpMethod.GET, null, byte[].class);
                MediaType contentType = getResponse.getHeaders().getContentType();
                if (contentType == null || (!contentType.includes(MediaType.IMAGE_JPEG) && !contentType.includes(MediaType.IMAGE_PNG))) {
                    log.error("[Validate] GET fallback image URL validation failed. Content-Type is {}", contentType);
                    throw new BusinessException(ErrorCode.VALIDATION_ERROR);
                }
            } catch (Exception fallbackEx) {
                log.error("[Validate] GET fallback failed for url={}. error={}", imageUrl, fallbackEx.getMessage());
                throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED);
            }
        }
    }

    public String createImageContainer(String instagramUserId, String accessToken, String imageUrl, String caption) {
        String normalizedImageUrl = normalizeImageUrl(imageUrl);
        log.info("[Publish] Normalized single image URL: {}", normalizedImageUrl);
        validateCloudFrontUrl(normalizedImageUrl);
        MultiValueMap<String, String> body = authenticatedBody(accessToken);
        body.add("image_url", normalizedImageUrl);
        addCaption(body, caption);
        String containerId = createContainer(instagramUserId, body);
        log.info("[Publish] Created single image container. containerId={}", containerId);
        return containerId;
    }

    public String createCarouselContainer(String instagramUserId, String accessToken, List<String> imageUrls, String caption) {
        List<String> children = imageUrls.stream()
                .map(imageUrl -> {
                    String normalizedImageUrl = normalizeImageUrl(imageUrl);
                    log.info("[Publish] Normalized carousel image URL: {}", normalizedImageUrl);
                    validateCloudFrontUrl(normalizedImageUrl);
                    String childId = createCarouselImageContainer(instagramUserId, accessToken, normalizedImageUrl);
                    log.info("[Publish] Created carousel child container. childId={}", childId);
                    return childId;
                })
                .toList();

        MultiValueMap<String, String> body = authenticatedBody(accessToken);
        body.add("media_type", "CAROUSEL");
        body.add("children", String.join(",", children));
        addCaption(body, caption);
        String parentId = createContainer(instagramUserId, body);
        log.info("[Publish] Created parent carousel container. parentId={}, children={}", parentId, children);
        return parentId;
    }

    public String createReelsContainer(String instagramUserId, String accessToken, String videoUrl, String caption) {
        log.error("[Publish] Reels publishing is disabled. This method should not be called.");
        throw new BusinessException(ErrorCode.INVALID_REQUEST);
    }

    public String getContainerStatus(String accessToken, String containerId) {
        try {
            Map<?, ?> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path(apiVersion + "/{containerId}")
                            .queryParam("fields", "status_code")
                            .queryParam("access_token", accessToken)
                            .build(containerId))
                    .retrieve()
                    .body(Map.class);
            Object statusCode = response != null ? response.get("status_code") : null;
            return statusCode instanceof String value ? value : "ERROR";
        } catch (RestClientResponseException exception) {
            handleMetaError("Instagram container status failed", exception);
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        } catch (RestClientException exception) {
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        }
    }

    public String publishContainer(String instagramUserId, String accessToken, String containerId) {
        MultiValueMap<String, String> body = authenticatedBody(accessToken);
        body.add("creation_id", containerId);
        try {
            Map<?, ?> response = postForm(apiVersion + "/" + instagramUserId + "/media_publish", body);
            Object id = response != null ? response.get("id") : null;
            if (id instanceof String value && !value.isBlank()) {
                log.info("[Publish] media_publish success. instagramMediaId={}", value);
                return value;
            }
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED);
        } catch (RestClientResponseException exception) {
            handleMetaError("Instagram media_publish failed", exception);
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        } catch (RestClientException exception) {
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        }
    }

    public String getPermalink(String accessToken, String mediaId) {
        try {
            Map<?, ?> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path(apiVersion + "/{mediaId}")
                            .queryParam("fields", "permalink")
                            .queryParam("access_token", accessToken)
                            .build(mediaId))
                    .retrieve()
                    .body(Map.class);
            Object permalink = response != null ? response.get("permalink") : null;
            if (permalink instanceof String value && !value.isBlank()) {
                log.info("[Publish] permalink lookup success. permalink={}", value);
                return value;
            }
            return "https://www.instagram.com/p/" + mediaId;
        } catch (RestClientResponseException exception) {
            handleMetaError("Instagram permalink lookup failed", exception);
            return "https://www.instagram.com/p/" + mediaId;
        } catch (RestClientException exception) {
            log.warn("Instagram permalink lookup failed for mediaId={}", mediaId);
            return "https://www.instagram.com/p/" + mediaId;
        }
    }

    private String createCarouselImageContainer(String instagramUserId, String accessToken, String imageUrl) {
        MultiValueMap<String, String> body = authenticatedBody(accessToken);
        body.add("image_url", imageUrl);
        body.add("is_carousel_item", "true");
        return createContainer(instagramUserId, body);
    }

    private String normalizeImageUrl(String imageUrl) {
        if (imageUrl == null || imageUrl.isBlank()) {
            throw new IllegalArgumentException("Instagram publish imageUrl is empty");
        }

        String trimmed = imageUrl.trim();

        if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
            return trimmed;
        }

        return "https://" + trimmed;
    }

    private String createContainer(String instagramUserId, MultiValueMap<String, String> body) {
        try {
            Map<?, ?> response = postForm(apiVersion + "/" + instagramUserId + "/media", body);
            Object id = response != null ? response.get("id") : null;
            if (id instanceof String value && !value.isBlank()) {
                return value;
            }
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED);
        } catch (RestClientResponseException exception) {
            handleMetaError("Instagram media container creation failed", exception);
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        } catch (RestClientException exception) {
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        }
    }

    private Map<?, ?> postForm(String path, MultiValueMap<String, String> body) {
        return restClient.post()
                .uri(path)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .body(body)
                .retrieve()
                .body(Map.class);
    }

    private MultiValueMap<String, String> authenticatedBody(String accessToken) {
        MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
        body.add("access_token", accessToken);
        return body;
    }

    private void addCaption(MultiValueMap<String, String> body, String caption) {
        if (caption != null && !caption.isBlank()) {
            body.add("caption", caption);
        }
    }

    private void handleMetaError(String messageContext, RestClientResponseException exception) {
        String bodyString = exception.getResponseBodyAsString();
        try {
            JsonNode root = objectMapper.readTree(bodyString);
            JsonNode errorNode = root.path("error");
            if (!errorNode.isMissingNode()) {
                log.error("[MetaError] {} - type: {}, code: {}, subcode: {}, fbtrace_id: {}, message: {}",
                        messageContext,
                        errorNode.path("type").asText("N/A"),
                        errorNode.path("code").asText("N/A"),
                        errorNode.path("error_subcode").asText("N/A"),
                        errorNode.path("fbtrace_id").asText("N/A"),
                        errorNode.path("message").asText("N/A"));
            } else {
                log.error("[MetaError] {} - raw response: {}", messageContext, bodyString);
            }
        } catch (JsonProcessingException e) {
            log.error("[MetaError] {} - raw response: {}", messageContext, bodyString);
        }
    }
}
