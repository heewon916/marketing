package com.matketing.be.global.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Swagger(OpenAPI) 설정 클래스
 *
 * API 문서화 및 테스트를 위한 Swagger UI 설정을 담당합니다.
 * JWT 토큰 기반 인증이 필요한 API를 Swagger UI에서 직접 테스트할 수 있도록
 * SecurityScheme(Bearer Token) 설정을 포함합니다.
 */
@Configuration
public class SwaggerConfig {

    /**
     * OpenAPI 빈을 등록하여 Swagger 문서의 기본 정보와 보안 설정을 구성합니다.
     *
     * @return 커스텀 설정이 적용된 OpenAPI 객체
     */
    @Bean
    public OpenAPI openAPI() {
        Info info = new Info()
                .title("Matketing API Document")
                .description("Matketing 프로젝트의 백엔드 API 명세서입니다.")
                .version("v1.0.0");

        // JWT 인증 스키마의 이름을 정의합니다.
        String jwtSchemeName = "jwtAuth";

        // SecurityRequirement를 통해 모든 API 요청에 기본적으로 JWT 인증이 필요함을 명시합니다.
        SecurityRequirement securityRequirement = new SecurityRequirement().addList(jwtSchemeName);

        // Components에 실제 JWT 인증 방식을 정의합니다.
        Components components = new Components()
                .addSecuritySchemes(jwtSchemeName, new SecurityScheme()
                        .name(jwtSchemeName)
                        .type(SecurityScheme.Type.HTTP) // HTTP 방식
                        .scheme("bearer")               // Bearer 방식
                        .bearerFormat("JWT"));          // 토큰 포맷이 JWT임을 명시

        // 위에서 설정한 정보, 보안 요구사항, 컴포넌트를 OpenAPI 객체에 조립하여 반환합니다.
        return new OpenAPI()
                .addServersItem(new Server().url("/"))
                .info(info)
                .addSecurityItem(securityRequirement)
                .components(components);
    }
}
