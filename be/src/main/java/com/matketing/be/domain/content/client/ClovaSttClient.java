package com.matketing.be.domain.content.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.matketing.be.domain.content.config.ClovaSttProperties;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.io.IOException;
import java.time.Duration;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@Component
public class ClovaSttClient {

    private final RestClient restClient;
    private final ClovaSttProperties properties;
    private final ObjectMapper objectMapper;
    private final ClovaSttAudioConverter audioConverter;

    public ClovaSttClient(
            RestClient.Builder builder,
            ClovaSttProperties properties,
            ObjectMapper objectMapper,
            ClovaSttAudioConverter audioConverter
    ) {
        // STT API도 외부 의존성이므로 연결/응답 timeout을 설정 파일에서 제어한다.
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofSeconds(properties.timeoutSeconds()));
        requestFactory.setReadTimeout(Duration.ofSeconds(properties.timeoutSeconds()));
        this.restClient = builder
                .requestFactory(requestFactory)
                .baseUrl(properties.baseUrl())
                .build();
        this.properties = properties;
        this.objectMapper = objectMapper;
        this.audioConverter = audioConverter;
    }

    /***
     * CLOVA Speech 단문 STT API에 오디오 파일을 전달하고, 인식된 텍스트를 반환받는 함수
     * @param audioFile 사용자의 음성 파일
     * @return 인식된 텍스트
     */
    public String recognize(MultipartFile audioFile) {
        try {
            validateProperties();
            byte[] audioBytes = audioConverter.toSupportedAudioBytes(audioFile);

            // CLOVA Speech 단문 STT는 POST /recog/v1/stt에 음성 바이너리를 그대로 싣는다.
            // 프론트 audio/webm은 호출 전에 WAV로 변환되어 여기에는 API가 처리 가능한 바이트만 들어온다.
            String responseBody = restClient.post()
                    .uri(uriBuilder -> {
                        uriBuilder.path("/stt")
                                .queryParam("lang", properties.lang());
                        if (properties.assessment()) {
                            uriBuilder.queryParam("assessment", true);
                        }
                        if (properties.utterance() != null && !properties.utterance().isBlank()) {
                            uriBuilder.queryParam("utterance", properties.utterance());
                        }
                        if (properties.boostings() != null && !properties.boostings().isBlank()) {
                            uriBuilder.queryParam("boostings", properties.boostings());
                        }
                        if (properties.graph()) {
                            uriBuilder.queryParam("graph", true);
                        }
                        return uriBuilder.build();
                    })
                    .header("X-CLOVASPEECH-API-KEY", properties.secretKey())
                    .contentType(MediaType.APPLICATION_OCTET_STREAM)
                    .body(audioBytes)
                    .retrieve()
                    .body(String.class);

            return parseUtterance(responseBody);
        } catch (BusinessException exception) {
            throw exception;
        } catch (RestClientResponseException exception) {
            log.warn(
                    "content.clova-stt.recognize.failed-response: status={}, body={}",
                    exception.getStatusCode(),
                    exception.getResponseBodyAsString(),
                    exception
            );
            throw new BusinessException(ErrorCode.STT_FAILED, exception);
        } catch (IOException | RestClientException exception) {
            log.warn("content.clova-stt.recognize.failed: Clova STT request failed.", exception);
            throw new BusinessException(ErrorCode.STT_FAILED, exception);
        } catch (Exception exception) {
            log.warn("content.clova-stt.recognize.invalid-response: response parsing failed.", exception);
            throw new BusinessException(ErrorCode.STT_PARSING_FAILED, exception);
        }
    }

    private void validateProperties() {
        if (properties.secretKey() == null || properties.secretKey().isBlank()) {
            log.warn("content.clova-stt.recognize.missing-credentials: CLOVA Speech secret key is not configured.");
            throw new BusinessException(ErrorCode.STT_FAILED);
        }
    }

    /***
     * CLOVA Speech 단문 STT 응답 본문에서 실제 발화 텍스트를 추출한다.
     * 단문 API의 표준 필드는 text이며, 기존 호환성을 위해 utterance/result도 보조로 확인한다.
     * 텍스트를 못 찾으면 정상 HTTP 응답이어도 STT 실패로 처리한다
     * @param responseBody
     * @return
     * @throws IOException
     */
    private String parseUtterance(String responseBody) throws IOException {
        if (responseBody == null || responseBody.isBlank()) {
            throw new BusinessException(ErrorCode.STT_FAILED);
        }

        // Clova 응답 필드명이 환경/버전에 따라 달라질 수 있어 알려진 텍스트 필드를 순서대로 탐색한다.
        JsonNode root = objectMapper.readTree(responseBody);
        String utterance = firstText(root, "text", "utterance", "result");
        if (utterance == null && root.path("result").isObject()) {
            utterance = firstText(root.path("result"), "text", "utterance");
        }
        if (utterance == null || utterance.isBlank()) {
            throw new BusinessException(ErrorCode.STT_FAILED);
        }
        return utterance;
    }

    // 후보 필드 중 문자열 값을 가진 첫 번째 필드를 반환한다.
    // JsonNode.path()를 사용해 없는 필드 접근에서도 NullPointerException이 나지 않게 한다.
    private String firstText(JsonNode node, String... fieldNames) {
        for (String fieldName : fieldNames) {
            JsonNode value = node.path(fieldName);
            if (value.isTextual()) {
                return value.asText();
            }
        }
        return null;
    }
}
