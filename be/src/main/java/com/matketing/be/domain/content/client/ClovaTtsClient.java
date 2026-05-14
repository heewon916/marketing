package com.matketing.be.domain.content.client;

import com.matketing.be.domain.content.config.ClovaTtsProperties;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Slf4j
@Component
public class ClovaTtsClient {

    private final RestClient restClient;
    private final ClovaTtsProperties properties;

    public ClovaTtsClient(RestClient.Builder builder, ClovaTtsProperties properties) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofSeconds(properties.timeoutSeconds()));
        requestFactory.setReadTimeout(Duration.ofSeconds(properties.timeoutSeconds()));

        this.restClient = builder
                .requestFactory(requestFactory)
                .baseUrl(properties.baseUrl())
                .build();
        this.properties = properties;
    }

    public byte[] synthesize(String text) {
        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("speaker", properties.speaker());
        formData.add("volume", "0");
        formData.add("speed", "0");
        formData.add("pitch", "0");
        formData.add("text", text);
        formData.add("format", "mp3");

        try {
            return restClient.post()
                    .header("X-NCP-APIGW-API-KEY-ID", properties.clientId())
                    .header("X-NCP-APIGW-API-KEY", properties.clientSecret())
                    .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                    .body(formData)
                    .retrieve()
                    .body(byte[].class);
        } catch (Exception exception) {
            log.error("Clova TTS request failed.", exception);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }
}
