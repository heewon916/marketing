package com.matketing.be.domain.analytic.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.matketing.be.domain.analytic.dto.MetaUserInsightsResult;
import java.io.IOException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

@Slf4j
@Component
public class MetaUserInsightsClient {

    private static final String BASE_URL = "https://graph.instagram.com/v25.0";

    private final RestClient restClient;
    private final ObjectMapper objectMapper;

    public MetaUserInsightsClient(RestClient.Builder builder, ObjectMapper objectMapper) {
        this.restClient = builder.baseUrl(BASE_URL).build();
        this.objectMapper = objectMapper;
    }

    public MetaUserInsightsResult fetchUserInsights(
            String instagramUserId,
            String accessToken,
            long since,
            long until
    ) {
        try {
            String responseBody = restClient.get()
                            .uri(uriBuilder -> uriBuilder.path("/{instagramUserId}/insights")
                            .queryParam("access_token", accessToken)
                            .queryParam("metric", "views,saves,shares")
                            .queryParam("period", "day")
                            .queryParam("metric_type", "total_value")
                            .queryParam("since", since)
                            .queryParam("until", until)
                            .build(instagramUserId))
                    .retrieve()
                    .body(String.class);

            return parse(responseBody);
        } catch (RestClientResponseException exception) {
            log.warn("meta.user-insights.failed-response: instagramUserId={}, status={}, body={}",
                    instagramUserId, exception.getStatusCode(),
                    redactAccessToken(exception.getResponseBodyAsString(), accessToken));
            throw new IllegalStateException("Meta User Insights API failed", exception);
        } catch (RestClientException | IOException exception) {
            log.warn("meta.user-insights.failed: instagramUserId={}, exceptionType={}",
                    instagramUserId, exception.getClass().getSimpleName());
            throw new IllegalStateException("Meta User Insights API failed", exception);
        }
    }

    private MetaUserInsightsResult parse(String responseBody) throws IOException {
        if (responseBody == null || responseBody.isBlank()) {
            return new MetaUserInsightsResult(0, 0, 0);
        }

        JsonNode data = objectMapper.readTree(responseBody).path("data");
        int views = 0;
        int saves = 0;
        int shares = 0;

        if (data.isArray()) {
            for (JsonNode item : data) {
                String name = item.path("name").asText("");
                int value = item.path("total_value").path("value").asInt(0);
                if ("views".equals(name)) {
                    views = value;
                } else if ("saves".equals(name)) {
                    saves = value;
                } else if ("shares".equals(name)) {
                    shares = value;
                }
            }
        }

        return new MetaUserInsightsResult(views, saves, shares);
    }

    private String redactAccessToken(String value, String accessToken) {
        if (value == null || accessToken == null || accessToken.isBlank()) {
            return value;
        }
        return value.replace(accessToken, "[REDACTED]");
    }
}
