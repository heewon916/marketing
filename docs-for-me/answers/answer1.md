# Instagram OAuth Login 구현 계획 (`GET /api/v1/users/instagram`)

현재 백엔드(Spring Boot 3.5 + Java 21) 환경에 맞추어 인스타그램 OAuth 로그인을 구현하기 위한 계획입니다. 팀 규칙을 반영하여 접속 주소 및 환경 변수 형식을 구성했습니다.

## 1. 사전 준비 (Meta for Developers)
1. [Meta for Developers](https://developers.facebook.com/)에서 앱 생성.
2. **Instagram Basic Display API** 제품 추가.
3. 유효한 OAuth 리디렉션 URI 설정 (실제 서비스 주소인 `http://k14a401.p.ssafy.io/api/v1/users/instagram/callback` 등).
4. `App ID` 및 `App Secret` 발급.

## 2. 의존성 추가 (be/build.gradle)
기존 `spring-boot-starter-security` 외에 OAuth2 클라이언트 기능을 사용하기 위한 의존성을 추가해야 합니다.
```gradle
dependencies {
    // 기존 의존성들...
    implementation 'org.springframework.boot:spring-boot-starter-oauth2-client'
}
```

## 3. 환경 변수 설정 (application.properties)
Instagram은 Spring Security에서 기본 제공하는 Provider가 아니므로, Client 정보와 Provider 정보를 모두 직접 설정해야 합니다. 현재 프로젝트의 설정 파일 형식에 맞게 `.properties`로 구성합니다.
```properties
spring.security.oauth2.client.registration.instagram.client-id=${INSTAGRAM_CLIENT_ID}
spring.security.oauth2.client.registration.instagram.client-secret=${INSTAGRAM_CLIENT_SECRET}
# 인가 코드를 받을 서버의 콜백 URL (팀 규칙 적용)
spring.security.oauth2.client.registration.instagram.redirect-uri=http://k14a401.p.ssafy.io/api/v1/users/instagram/callback
spring.security.oauth2.client.registration.instagram.authorization-grant-type=authorization_code
spring.security.oauth2.client.registration.instagram.scope=user_profile,user_media
spring.security.oauth2.client.registration.instagram.client-name=Instagram

spring.security.oauth2.client.provider.instagram.authorization-uri=https://api.instagram.com/oauth/authorize
spring.security.oauth2.client.provider.instagram.token-uri=https://api.instagram.com/oauth/access_token
spring.security.oauth2.client.provider.instagram.user-info-uri=https://graph.instagram.com/me?fields=id,username
spring.security.oauth2.client.provider.instagram.user-name-attribute=id
```

## 4. Security Configuration 설정
요청하신 `GET /api/v1/users/instagram` 경로를 로그인 시작 엔드포인트로 사용하도록 커스터마이징합니다.

```java
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final CustomOAuth2UserService customOAuth2UserService;
    private final OAuth2AuthenticationSuccessHandler successHandler;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/users/instagram", "/api/v1/users/instagram/callback").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2Login(oauth2 -> oauth2
                // 1. 로그인 인가 요청 시작점 커스터마이징 (GET /api/v1/users/instagram)
                .authorizationEndpoint(authEndpoint -> authEndpoint
                    // baseUri를 /api/v1/users 로 설정하면 뒤에 {registrationId}가 붙어
                    // /api/v1/users/instagram 경로가 완성됩니다.
                    .baseUri("/api/v1/users")
                )
                // 2. 인가 코드 콜백 엔드포인트 커스터마이징
                .redirectionEndpoint(redirectionEndpoint -> redirectionEndpoint
                    .baseUri("/api/v1/users/*/callback")
                )
                // 3. 사용자 정보 획득 후 처리
                .userInfoEndpoint(userInfo -> userInfo
                    .userService(customOAuth2UserService)
                )
                // 4. 로그인 성공 후 후처리 (JWT 발급 등)
                .successHandler(successHandler)
            );

        return http.build();
    }
}
```

## 5. 동작 흐름 (Flow)
1. **[FE -> BE]**: 사용자가 로그인 버튼 클릭 시 `GET /api/v1/users/instagram` 주소로 이동(또는 리디렉트).
2. **[BE -> Instagram]**: Spring Security가 가로채서 설정된 `authorization-uri`를 이용해 인스타그램 로그인 창으로 HTTP 302 리디렉트.
3. **[사용자]**: 인스타그램 로그인 및 앱 권한 제공 동의.
4. **[Instagram -> BE]**: 등록된 리디렉트 URI(`http://k14a401.p.ssafy.io/api/v1/users/instagram/callback`)로 인가 코드(Code) 전송.
5. **[BE -> Instagram]**: Spring Security가 인가 코드를 가지고 `token-uri`를 호출해 Access Token 발급. 이어서 `user-info-uri`를 호출해 사용자 정보(ID, Username 등) 획득.
6. **[BE 내부 - CustomOAuth2UserService]**: 획득한 정보로 DB를 조회하여 신규 유저면 회원가입 처리를, 기존 유저면 정보를 업데이트. (`OAuth2User` 객체 반환)
7. **[BE -> FE - SuccessHandler]**: 성공 핸들러에서 자체 서비스용 JWT(Access/Refresh Token)를 생성. 그 후 프론트엔드의 콜백 페이지(`http://k14a401.p.ssafy.io/auth/callback?token=...`)로 302 리디렉트하여 토큰을 전달.

### 더 자세한 동작 흐름(1차)
/api/v1/users/instagram API는 직접 작성한 특정 Controller 파일을 거치는 것이 아니라, Spring Security OAuth2 Client 라이브러리가 기본적으로 제공하는
필터(Filter)와 설정된 파일들을 거치며 실행됩니다.

사용자가 인스타그램 로그인을 클릭했을 때부터 최종적으로 콜백 처리되는 과정까지 거치는 파일들의 실행 흐름은 다음과 같습니다.

1️⃣ 로그인 진입 (사용자 -> Nginx -> Spring Security)
* nginx/conf.d/default.conf
    - 사용자가 프론트엔드에서 버튼을 클릭해 http://localhost/api/v1/users/instagram으로 요청을 보냅니다.
    - Nginx가 이 요청을 가로채서 proxy_pass http://spring:8080/api/... 를 통해 백엔드(Spring) 컨테이너로 전달합니다.

* SecurityConfig.java (보안 설정)
    - 요청이 백엔드에 도착하면 가장 먼저 Spring Security의 필터 체인(SecurityFilterChain)을 거칩니다.
    - 이 파일에서 .oauth2Login(oauth2 -> oauth2.authorizationEndpoint(...)) 설정에 의해 기본 OAuth 로그인 진입점 주소가 /oauth2/authorization/에서 /api/v1/users/로
      변경되어 있습니다.
    - 따라서 /api/v1/users/instagram 요청을 OAuth2AuthorizationRequestRedirectFilter라는 기본 내장 필터가 가로챕니다.

* application.properties (OAuth 설정 읽기)
    - 필터는 application.properties에 등록된 인스타그램의 client-id, client-secret, scope, 그리고 authorization-uri (https://api.instagram.com/oauth/authorize) 등의
      정보를 읽어옵니다.
    - 이 정보를 바탕으로 인스타그램의 실제 로그인 페이지 URL을 생성한 뒤, 사용자에게 HTTP 302 리다이렉트(Redirect) 응답을 보냅니다. (우리가 테스트에서 확인한 부분입니다)

  ---

2️⃣ 인스타그램에서 로그인 후 콜백 (Instagram -> Spring Security)
사용자가 인스타그램 창에서 아이디/비밀번호를 입력하고 로그인을 성공하면, 인스타그램이 설정된 리다이렉트
주소(http://k14a401.p.ssafy.io/api/v1/users/instagram/callback)로 인가 코드(Authorization Code)와 함께 다시 요청을 보냅니다.

* SecurityConfig.java (콜백 수신)
    - .redirectionEndpoint(redirectionEndpoint -> redirectionEndpoint.baseUri("/api/v1/users/*/callback")) 설정에 의해, 이 콜백 요청은
      OAuth2LoginAuthenticationFilter라는 필터가 가로챕니다.
    - 필터는 인가 코드를 이용해 인스타그램 서버와 통신하여 Access Token을 받아옵니다.

* application.properties (유저 정보 요청)
    - Access Token을 받은 직후, 필터는 user-info-uri (https://graph.instagram.com/me?fields=id,username)로 한 번 더 요청을 보내 인스타그램 사용자의 아이디(id)와
      닉네임(username)을 가져옵니다.

  ---

3️⃣ 유저 정보 DB 저장 및 서비스 토큰 발급 (Custom 로직 실행)
이제 우리가 직접 작성한 파일들이 실행될 차례입니다.

* CustomOAuth2UserService.java (유저 정보 처리)
    - SecurityConfig에 .userInfoEndpoint(userInfo -> userInfo.userService(customOAuth2UserService))로 등록해둔 이 클래스의 loadUser() 메서드가 실행됩니다.
    - 인스타그램에서 받아온 유저 정보(id, username)를 꺼냅니다.
    - UserRepository.java 를 통해 해당 id(providerId)가 DB에 존재하는지 확인합니다.
    - 존재하면 이름을 업데이트하고, 없으면 신규 회원으로 User.java 엔티티를 생성하여 DB에 저장합니다.

* OAuth2AuthenticationSuccessHandler.java (로그인 최종 성공)
    - 회원 정보 저장이 끝나면 로그인이 성공한 것으로 간주되어 이 핸들러의 onAuthenticationSuccess() 메서드가 실행됩니다.
    - JwtTokenProvider.java: 이 클래스를 호출해 우리 서비스 전용 Access Token과 Refresh Token을 새로 발급합니다.
    - RefreshTokenRepository.java: 발급된 Refresh Token을 Redis에 저장합니다.
    - 최종적으로 발급된 Access Token을 URL 쿼리 파라미터로 붙여서, 프론트엔드의 화면(http://k14a401.p.ssafy.io/auth/callback?token=...)으로 HTTP 302 리다이렉트 시킵니다.

이렇게 Spring Security의 기본 필터들과 작성하신 커스텀 파일들이 유기적으로 연결되어 전체 OAuth 과정이 완성됩니다.

### 더 자세한 동작 흐름(2차)
🚪 1단계: 로그인 진입 및 문표 발급 (SecurityConfig.java)
사용자가 프론트엔드 화면에서 "인스타그램으로 로그인" 버튼을 누릅니다.
1. 버튼을 누르면 우리 백엔드의 https://localhost/api/v1/users/instagram 주소로 이동합니다.
2. 백엔드의 보초병(SecurityConfig.java)이 이 요청을 확인합니다.
3. 보초병은 "아, 인스타그램 로그인하러 왔구나!" 하고, 해킹(CSRF)을 방지하기 위해 사용자 브라우저에 임시 암호(state)를 몰래 쥐여줍니다.
4. 그리고 .env 파일에 적힌 우리의 인스타그램 앱 아이디(client-id)와 콜백 주소(redirect-uri), 그리고 요구하는 권한(scope: 비즈니스 권한 5개)을 바리바리 싸 들고,
   사용자를 진짜 인스타그램 로그인 페이지(https://api.instagram.com/oauth/authorize...)로 자동 이동(Redirect) 시킵니다.

  ---

🎟️ 2단계: 인스타그램 승인 및 콜백 (다시 백엔드로)
사용자가 인스타그램 화면에서 본인 아이디/비밀번호를 치고 "권한 허용(Continue)" 버튼을 누릅니다.
1. 인스타그램 서버가 "응, 얘 정상 유저 맞네!" 하고 확인한 뒤, 아까 우리가 등록해둔 백엔드 콜백 주소(https://localhost/api/v1/users/instagram/callback)로 사용자를 다시
   돌려보냅니다.
2. 이때 그냥 돌려보내지 않고, 임시 인가 코드(Code) 와 아까 우리가 발급했던 임시 암호(state)를 꼬리표로 달아서 보냅니다.
3. 백엔드 보초병은 돌아온 사용자의 암호(state)를 확인하고, 일치하면 그 인가 코드(Code)를 가로챕니다.

  ---

🏥 3단계: 진짜 토큰으로 교환 및 심폐소생술 (InstaTokenConverter.java)
인가 코드(Code)는 말 그대로 '임시 교환권'일 뿐입니다. 이제 진짜 출입증(Access Token)으로 바꿔야 합니다.
1. 백엔드 보초병이 인스타그램 서버 뒷문(https://api.instagram.com/oauth/access_token)으로 몰래 찾아가서 "아까 그 교환권 줄 테니, 진짜 토큰 줘!" 하고 요청합니다.
2. 인스타그램 서버가 진짜 토큰을 주는데, 아까 겪었던 그 문제처럼 표준 규격(token_type: "Bearer")을 빼먹고 줍니다.
3. 이때 우리가 직접 만든 응급 구조대 InstaTokenConverter.java 가 출동합니다!
4. 구조대가 에러가 터지기 직전에 반쪽짜리 토큰을 가로채서, 겉포장지에 "이거 Bearer 타입 맞음!" 이라고 강제로 도장을 찍어(심폐소생술) 규격에 맞게 완벽하게 포장해
   줍니다.

  ---

💾 4단계: 유저 정보 조회 및 DB 저장 (OAuthUserService.java)
이제 완벽한 토큰을 얻었으니, 이 토큰을 들고 인스타그램에 "이 유저 누군지 프로필 좀 줘봐!" 하고 물어봅니다.
1. 우리가 만든 OAuthUserService.java 파일이 작동하기 시작합니다.
2. 인스타그램이 유저의 고유 아이디(id)와 이름(username)을 대답해 줍니다.
3. 코드는 UserRepository에게 "혹시 우리 DB(matketing_db의 users 테이블)에 이 id를 가진 애가 예전에 가입한 적 있어?" 라고 물어봅니다.
    * 만약 처음 온 유저라면 (신규 가입): 방금 우리가 기획서대로 고친(UUID, 토큰 만료 시간 등) 새로운 User 데이터베이스 칸을 만들어서 인스타그램 정보를 저장합니다.
    * 만약 예전에 왔던 유저라면 (기존 회원): 혹시 그사이에 인스타그램 닉네임이 바뀌었을 수도 있으니 정보만 최신으로 업데이트(update) 해줍니다.

  ---

🎁 5단계: 우리 서비스 전용 토큰 발급 및 프론트엔드로 리다이렉트 (OAuthSuccessHandler.java, JwtTokenProvider.java)
이제 DB 저장까지 다 끝났으니, 인스타그램 토큰은 서랍에 넣어두고 우리 서비스(마케팅 플랫폼)만의 전용 자유이용권을 만들어 줄 차례입니다.
1. 로그인이 최종 성공하면 OAuthSuccessHandler.java 파일이 실행됩니다.
2. JwtTokenProvider.java 가 .env에 있는 비밀번호(JWT_SECRET)를 이용해 두 가지 토큰을 찍어냅니다.
    * Access Token (짧은 수명): 사용자가 들고 다닐 자유이용권
    * Refresh Token (긴 수명 14일): 나중에 Access Token이 만료되면 새로 발급받을 때 쓸 보증수표
3. 보안을 위해 Refresh Token은 유저에게 주지 않고, 백엔드 내부의 비밀 금고인 Redis 데이터베이스(refreshTokenRepository)에 몰래 저장합니다.
4. 마지막으로, 사용자가 쓸 Access Token만 주소창 꼬리표(?token=...)로 예쁘게 달아서, .env에 설정된 프론트엔드 주소(FRONTEND_URL, 지금은 테스트용 naver.com) 로 사용자를
   최종적으로 튕겨(Redirect) 보냅니다.


## 6. 추가 구현이 필요한 클래스

### 1) CustomOAuth2UserService
```java
@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {
    private final UserRepository userRepository;

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);

        // Instagram에서 받은 사용자 정보 추출
        Map<String, Object> attributes = oAuth2User.getAttributes();
        String providerId = attributes.get("id").toString();
        String username = attributes.get("username").toString();

        // DB 확인 후 신규 유저 등록 또는 기존 유저 업데이트 로직
        // User user = userRepository.findByProviderId(providerId).orElse(...);

        return new DefaultOAuth2User(
                Collections.singleton(new SimpleGrantedAuthority("ROLE_USER")),
                attributes,
                "id"
        );
    }
}
```

### 2) OAuth2AuthenticationSuccessHandler
```java
@Component
@RequiredArgsConstructor
public class OAuth2AuthenticationSuccessHandler extends SimpleUrlAuthenticationSuccessHandler {
    private final JwtTokenProvider jwtTokenProvider;

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response,
                                        Authentication authentication) throws IOException, ServletException {

        OAuth2User oAuth2User = (OAuth2User) authentication.getPrincipal();
        // JWT 발급 로직
        String accessToken = jwtTokenProvider.createAccessToken(authentication);

        // Redis를 사용 중이시므로 RefreshToken 생성 및 저장 로직도 이곳에 추가

        // 프론트엔드 리디렉트 (팀 규칙 적용)
        String targetUrl = UriComponentsBuilder.fromUriString("http://k14a401.p.ssafy.io/auth/callback")
                .queryParam("token", accessToken)
                .build().toUriString();

        getRedirectStrategy().sendRedirect(request, response, targetUrl);
    }
}
```

## 7. 주의사항 및 참고
- 팀 규칙에 따라 `.env` 파일 등에 환경 변수(`INSTAGRAM_CLIENT_ID`, `INSTAGRAM_CLIENT_SECRET`) 추가 시 Notion 공유 및 인프라 담당자에게 전달(Jenkins Credentials의 `marketing-env` 수정)해야 합니다.
- 외부 접속 주소(http://k14a401.p.ssafy.io)를 기준으로 리디렉트 URI가 설정되어 있으므로, 인스타그램 개발자 콘솔에서도 해당 주소와 포트 등을 정확히 등록해야 합니다.

## 8. 구현을 위한 To-Do 리스트 (Action Items)
- [x] **Meta for Developers 설정**
  - [x] Instagram Basic Display API 앱 생성 및 설정
  - [x] 리디렉션 URI (`http://k14a401.p.ssafy.io/api/v1/users/instagram/callback`) 등록
  - [x] `INSTAGRAM_CLIENT_ID`, `INSTAGRAM_CLIENT_SECRET` 발급
- [ ] **환경 변수 관리 (팀 규칙 적용)**
  - [x] 개발 환경 `.env` 에 `INSTAGRAM_CLIENT_ID`, `INSTAGRAM_CLIENT_SECRET` 추가
  - [ ] **Notion**에 신규 환경 변수 즉시 공유
  - [ ] **인프라 담당자**에게 알림 (Jenkins Credentials `marketing-env` 값 수정 요청)
- [x] **백엔드 (Spring Boot) 구현**
  - [x] `be/build.gradle`에 `spring-boot-starter-oauth2-client` 의존성 추가
  - [x] `be/src/main/resources/application.properties`에 인스타그램 OAuth2 설정 추가
  - [x] `SecurityConfig.java` 생성 및 OAuth2 로그인 엔드포인트 커스텀 (`GET /api/v1/users/instagram`)
  - [x] `CustomOAuth2UserService.java` 구현 (인스타그램 사용자 정보 DB 저장/조회 로직)
  - [x] `OAuth2AuthenticationSuccessHandler.java` 구현 (JWT 생성 및 프론트엔드 리디렉트 로직)
  - [x] JWT 생성 및 검증을 위한 `JwtTokenProvider` 구현
  - [x] Redis를 활용한 RefreshToken 저장 로직 구현 (팀 규칙 적용: `redis:6379`)
- [ ] **테스트 및 검증**
  - [ ] 인스타그램 로그인 전체 흐름(리디렉트 -> 인가 코드 -> 토큰 -> DB 저장 -> 프론트콜백) 정상 동작 확인
