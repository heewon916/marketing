package com.matketing.be.domain.content.client;

import org.springframework.stereotype.Component;

@Component
public class InstagramPublishClient {

    /*
     * Instagram Graph API 발행 클라이언트 설계 메모.
     *
     * domain/user 흐름에서 OAuth 로그인 시 users.access_token에 Instagram access token이 저장된다.
     * 실제 구현 시 publish/status 단계에서 인증 사용자 또는 content.store_id -> user_id를 통해 users row를 조회하고,
     * user.accessToken을 사용해 Instagram Content Publishing API를 호출한다.
     *
     * 예상 단계:
     * 1. users.access_token 조회
     * 2. Redis contents:{sessionId}의 caption, photo:* URL 목록 조회
     * 3. Instagram media container 생성
     * 4. container publish 호출
     * 5. 응답 media id, permalink를 ContentPublishStatusResponseDto와 DB contents에 저장
     *
     * 요청에 따라 실제 API 호출 코드는 아직 작성하지 않는다.
     */
}
