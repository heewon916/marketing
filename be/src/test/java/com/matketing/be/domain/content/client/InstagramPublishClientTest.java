package com.matketing.be.domain.content.client;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withRawStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

@ExtendWith(MockitoExtension.class)
class InstagramPublishClientTest {

    private InstagramPublishClient instagramPublishClient;
    private MockRestServiceServer mockServer;
    private MockRestServiceServer restTemplateMockServer;

    @BeforeEach
    void setUp() {
        RestClient.Builder builder = RestClient.builder();
        ObjectMapper objectMapper = new ObjectMapper();
        
        this.mockServer = MockRestServiceServer.bindTo(builder).build();
        
        org.springframework.web.client.RestTemplate restTemplate = new org.springframework.web.client.RestTemplate();
        this.restTemplateMockServer = MockRestServiceServer.bindTo(restTemplate).build();
        
        org.springframework.boot.web.client.RestTemplateBuilder restTemplateBuilder = org.mockito.Mockito.mock(org.springframework.boot.web.client.RestTemplateBuilder.class);
        org.mockito.Mockito.when(restTemplateBuilder.build()).thenReturn(restTemplate);
        
        instagramPublishClient = new InstagramPublishClient(
                builder,
                restTemplateBuilder,
                "https://graph.instagram.com",
                "v25.0",
                objectMapper
        );
    }

    @Test
    void getContainerStatusThrowsExceptionAndParsesMetaErrorWhenFailed() {
        String errorJson = """
                {
                    "error": {
                        "message": "Invalid OAuth access token.",
                        "type": "OAuthException",
                        "code": 190,
                        "error_subcode": 460,
                        "fbtrace_id": "AsomeTraceId123"
                    }
                }
                """;

        mockServer.expect(requestTo("https://graph.instagram.com/v25.0/test-container-id?fields=status_code&access_token=test-token"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withRawStatus(400)
                        .contentType(MediaType.APPLICATION_JSON)
                        .body(errorJson));

        assertThatThrownBy(() -> instagramPublishClient.getContainerStatus("test-token", "test-container-id"))
                .isInstanceOf(BusinessException.class)
                .hasMessageContaining("인스타그램 발행에 실패했습니다.");
                
        mockServer.verify();
    }
    
    @Test
    void createImageContainerThrowsExceptionWhenMetaReturnsError() {
        String errorJson = """
                {
                    "error": {
                        "message": "The image url is invalid.",
                        "type": "OAuthException",
                        "code": 100,
                        "fbtrace_id": "AsomeTraceId123"
                    }
                }
                """;

        // Mock CloudFront validation
        restTemplateMockServer.expect(requestTo("https://cdn.example.com/photo.jpg"))
                .andExpect(method(HttpMethod.HEAD))
                .andRespond(withSuccess().contentType(MediaType.IMAGE_JPEG));

        // Mock Meta API call
        mockServer.expect(requestTo("https://graph.instagram.com/v25.0/test-ig-user/media"))
                .andExpect(method(HttpMethod.POST))
                .andRespond(withRawStatus(400)
                        .contentType(MediaType.APPLICATION_JSON)
                        .body(errorJson));

        assertThatThrownBy(() -> instagramPublishClient.createImageContainer("test-ig-user", "test-token", "https://cdn.example.com/photo.jpg", "caption"))
                .isInstanceOf(BusinessException.class)
                .hasMessageContaining("인스타그램 발행에 실패했습니다.");
                
        restTemplateMockServer.verify();
        mockServer.verify();
    }
    
    @Test
    void getPermalinkReturnsUrlWhenSuccessful() {
        String responseJson = """
                {
                    "id": "123456",
                    "permalink": "https://instagram.com/p/123456"
                }
                """;
                
        mockServer.expect(requestTo("https://graph.instagram.com/v25.0/123456?fields=permalink&access_token=test-token"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess(responseJson, MediaType.APPLICATION_JSON));
                
        String permalink = instagramPublishClient.getPermalink("test-token", "123456");
        
        org.assertj.core.api.Assertions.assertThat(permalink).isEqualTo("https://instagram.com/p/123456");
        mockServer.verify();
    }
}
