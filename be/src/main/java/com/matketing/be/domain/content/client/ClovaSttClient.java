package com.matketing.be.domain.content.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.matketing.be.domain.content.config.ClovaSttProperties;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.io.IOException;
import java.time.Duration;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@Component
public class ClovaSttClient {

    private final RestClient restClient;
    private final ClovaSttProperties properties;
    private final ObjectMapper objectMapper;

    public ClovaSttClient(RestClient.Builder builder, ClovaSttProperties properties, ObjectMapper objectMapper) {
        // STT API도 외부 의존성이므로 연결/응답 timeout을 설정 파일에서 제어한다.
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofSeconds(properties.timeoutSeconds()));
        requestFactory.setReadTimeout(Duration.ofSeconds(properties.timeoutSeconds()));
        RestClient.Builder restClientBuilder = builder.requestFactory(requestFactory);
        if (properties.baseUrl() != null && !properties.baseUrl().isBlank()) {
            restClientBuilder.baseUrl(properties.baseUrl());
        }
        this.restClient = restClientBuilder.build();
        this.properties = properties;
        this.objectMapper = objectMapper;
    }

    /***
     * Clova STT API에 오디오 파일을 전달하고, 인식된 텍스트를 반환받는 함수
     * @param audioFile 사용자의 음성 파일
     * @return 인식된 텍스트
     */
    public String recognize(MultipartFile audioFile) {
        try {
            // 1. ByteArrayResource는 기본 파일명이 없어 multipart filename을 별도 Resource에서 보존한다.
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("media", new MultipartByteArrayResource(audioFile.getBytes(), audioFile.getOriginalFilename()));

            // 2. Clova STT에 multipart media로 전달한다
            String responseBody = restClient.post()
                    .header("X-CLOVASPEECH-API-KEY", properties.secretKey())
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(body)
                    .retrieve()
                    .body(String.class);

            // 3. Clova 응답에서 text, utterance, result 중 텍스트를 추출한다
            return parseUtterance(responseBody);
        } catch (BusinessException exception) {
            throw exception;
        } catch (IOException | RestClientException exception) {
            log.warn("content.clova-stt.recognize.failed: Clova STT request failed.", exception);
            throw new BusinessException(ErrorCode.STT_FAILED, exception);
        } catch (Exception exception) {
            log.warn("content.clova-stt.recognize.invalid-response: response parsing failed.", exception);
            throw new BusinessException(ErrorCode.STT_PARSING_FAILED, exception);
        }
    }

    /***
     * Clover 응답 본문에서 실제 발화 텍스트를 추출한다
     * 운영 환경의 응답 필드가 text/utterance/result 중 무엇인지 달라질 수 있어 여러 후보를 순서대로 확인한다.
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

    private static class MultipartByteArrayResource extends ByteArrayResource {

        private final String filename;

        // ByteArrayResource는 파일명을 제공하지 않으므로 multipart 업로드용 파일명을 별도로 들고 있는 Resource다.
        private MultipartByteArrayResource(byte[] byteArray, String filename) {
            super(byteArray);
            this.filename = filename == null || filename.isBlank() ? "audio" : filename;
        }

        @Override
        public String getFilename() {
            // RestClient의 multipart encoder가 Content-Disposition filename을 만들 수 있게 한다.
            return filename;
        }
    }
}
