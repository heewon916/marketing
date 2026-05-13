package com.matketing.be.domain.content.client;

import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

@Component
@Slf4j
public class InstagramPublishClient {

    private final RestClient restClient;

    public InstagramPublishClient(
            RestClient.Builder builder,
            @Value("${instagram.publish.base-url:https://graph.instagram.com}") String baseUrl
    ) {
        this.restClient = builder.baseUrl(baseUrl).build();
    }

    public String createImageContainer(String instagramUserId, String accessToken, String imageUrl, String caption) {
        MultiValueMap<String, String> body = authenticatedBody(accessToken);
        body.add("image_url", imageUrl);
        addCaption(body, caption);
        return createContainer(instagramUserId, body);
    }

    public String createCarouselContainer(String instagramUserId, String accessToken, List<String> imageUrls, String caption) {
        List<String> children = imageUrls.stream()
                .map(imageUrl -> createCarouselImageContainer(instagramUserId, accessToken, imageUrl))
                .toList();

        MultiValueMap<String, String> body = authenticatedBody(accessToken);
        body.add("media_type", "CAROUSEL");
        body.add("children", String.join(",", children));
        addCaption(body, caption);
        return createContainer(instagramUserId, body);
    }

    public String createReelsContainer(String instagramUserId, String accessToken, String videoUrl, String caption) {
        MultiValueMap<String, String> body = authenticatedBody(accessToken);
        body.add("media_type", "REELS");
        body.add("video_url", videoUrl);
        body.add("share_to_feed", "true");
        addCaption(body, caption);
        return createContainer(instagramUserId, body);
    }

    public String getContainerStatus(String accessToken, String containerId) {
        try {
            Map<?, ?> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/{containerId}")
                            .queryParam("fields", "status_code")
                            .queryParam("access_token", accessToken)
                            .build(containerId))
                    .retrieve()
                    .body(Map.class);
            Object statusCode = response != null ? response.get("status_code") : null;
            return statusCode instanceof String value ? value : "ERROR";
        } catch (RestClientResponseException exception) {
            log.warn("Instagram container status failed: {}", exception.getResponseBodyAsString());
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        } catch (RestClientException exception) {
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        }
    }

    public String publishContainer(String instagramUserId, String accessToken, String containerId) {
        MultiValueMap<String, String> body = authenticatedBody(accessToken);
        body.add("creation_id", containerId);
        try {
            Map<?, ?> response = postForm("/" + instagramUserId + "/media_publish", body);
            Object id = response != null ? response.get("id") : null;
            if (id instanceof String value && !value.isBlank()) {
                return value;
            }
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED);
        } catch (RestClientResponseException exception) {
            log.warn("Instagram media_publish failed: {}", exception.getResponseBodyAsString());
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        } catch (RestClientException exception) {
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED, exception);
        }
    }

    public String getPermalink(String accessToken, String mediaId) {
        try {
            Map<?, ?> response = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/{mediaId}")
                            .queryParam("fields", "permalink")
                            .queryParam("access_token", accessToken)
                            .build(mediaId))
                    .retrieve()
                    .body(Map.class);
            Object permalink = response != null ? response.get("permalink") : null;
            return permalink instanceof String value && !value.isBlank()
                    ? value
                    : "https://www.instagram.com/p/" + mediaId;
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

    private String createContainer(String instagramUserId, MultiValueMap<String, String> body) {
        try {
            Map<?, ?> response = postForm("/" + instagramUserId + "/media", body);
            Object id = response != null ? response.get("id") : null;
            if (id instanceof String value && !value.isBlank()) {
                return value;
            }
            throw new BusinessException(ErrorCode.INSTAGRAM_PUBLISH_FAILED);
        } catch (RestClientResponseException exception) {
            log.warn("Instagram media container creation failed: {}", exception.getResponseBodyAsString());
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
}
