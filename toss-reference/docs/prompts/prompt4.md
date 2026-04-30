토스 POS 플러그인(탭 화면 방식) 개발에서 가맹점 식별 정보(merchantId)와 연동에 필요한 토큰(accessToken)을 가져오는 방법은 크게 클라이언트 SDK를 통한 추출과 서버 간 연동(OAuth/API Key) 두 가지 관점으로 나뉩니다.

1. 클라이언트 SDK에서 가져오기 (가장 일반적인 방법)
플러그인이 POS 단말기 내에서 실행될 때, pos-plugin-sdk는 현재 플러그인이 구동 중인 가맹점의 정보를 제공합니다.

가맹점 ID (merchantId) 추출:
sdk.getMerchant() 메서드를 호출하면 현재 POS의 가맹점 정보(ID, 이름, 사업자 번호 등)를 담은 객체를 반환합니다.

JavaScript
const merchant = await sdk.getMerchant();
const merchantId = merchant.id; // 가맹점의 고유 ID
console.log("현재 가맹점 ID:", merchantId);
액세스 토큰 (accessToken) 추출:
플러그인에서 자체 백엔드 서버로 가맹점 인증 정보를 보낼 때 필요한 세션 토큰은 sdk.getAccessToken()을 통해 얻을 수 있습니다. 이는 Toss POS가 해당 플러그인 세션을 보증하는 토큰입니다.

JavaScript
const accessToken = await sdk.getAccessToken();
// 이 토큰을 백엔드로 보내 가맹점 인증을 수행합니다.
2. 서버 간 연동용 API Key (관리자 센터)
만약 POS 단말기가 아닌, 질문자님의 백엔드 서버에서 토스플레이스 API를 직접 호출하기 위한 영구적인 권한이 필요하다면 토스플레이스 개발자 센터에서 설정해야 합니다.

토스플레이스 개발자 센터 접속

내 플러그인 -> API 설정 메뉴로 이동

Client ID와 Client Secret (또는 발급된 API Key) 확인

이 키들을 사용하여 서버 환경변수에 저장하고, 토스플레이스 서버와 통신할 때 사용합니다.

3. 연동 플로우 요약
6자리 난수 확인까지 구현하셨다면, 마지막으로 이 정보를 백엔드에 저장하거나 매칭할 때 아래와 같은 흐름을 타게 됩니다.

POS 앱: sdk.getMerchant()로 merchantId 획득.

POS 앱: sdk.getAccessToken()으로 현재 세션의 token 획득.

POS 앱 -> 질문자님 서버: merchantId, token, 그리고 입력받은 6자리 난수를 전송.

질문자님 서버: 전달받은 정보를 통해 "어느 가맹점에서 누가 난수 인증을 완료했는지"를 확정하고 DB를 업데이트합니다.