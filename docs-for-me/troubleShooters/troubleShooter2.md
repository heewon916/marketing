# TroubleShooting & Concepts Log (Session 2)

이 문서는 인스타그램 소셜 로그인(OAuth2) 백엔드 연동 과정에서 발생한 주요 문제 해결 과정과, 새롭게 학습한 개념들을 정리한 문서입니다.

---

## 🛠️ 트러블슈팅 (문제 해결)

### 1. Java 파일 인코딩 에러 (컴파일 실패)
* **증상**: Docker로 Spring Boot 앱을 빌드할 때 `unmappable character for encoding UTF-8` 에러 발생.
* **원인**: Java 코드 내의 한글 주석이 `EUC-KR` 또는 `CP949`로 인코딩되어 있어 Linux(Docker) 환경의 기본 인코딩인 UTF-8과 충돌함.
* **해결**: Python 스크립트를 사용하여 `be/src/main/java` 내부의 모든 `.java` 파일을 UTF-8 인코딩으로 일괄 변환함.

### 2. Spring 컨테이너 DB 연결 실패 (Connection refused)
* **증상**: Spring 컨테이너가 켜지자마자 꺼지고, 로그에 PostgreSQL `Connection refused` 발생.
* **원인**: `compose.yaml`의 백엔드 환경 변수 `SPRING_DATASOURCE_URL`이 `localhost`로 되어 있어, 도커 컨테이너 내부 네트워크망의 `postgres` 컨테이너를 찾지 못함.
* **해결**: URL을 `jdbc:postgresql://postgres:5432/...` 로 수정하고, 달러 기호 이스케이프(`$$`) 처리 및 `SPRING_DATA_REDIS_HOST=redis` 환경 변수를 명시적으로 추가함.

### 3. 인스타그램 "Invalid platform app" 에러
* **증상**: 생성된 인스타그램 로그인 URL 접속 시 위와 같은 에러 텍스트 표출.
* **원인**: `.env`의 `INSTAGRAM_CLIENT_ID`에 'Facebook 앱 ID'가 잘못 입력됨.
* **해결**: Meta 개발자 센터의 'Instagram Basic Display' 탭에서 실제 **'Instagram 앱 ID'** (`1500529101780698`)를 발급받아 교체함.

### 4. 로컬 환경 빌드 실패 (DB/Redis 포트 접근 불가)
* **증상**: 터미널에서 `.\gradlew.bat build` 시 테스트 단계에서 DB 연결 실패.
* **원인**: `compose.yaml`에서 DB와 Redis가 도커 내부망(`expose`)으로만 열려 있고, 호스트 PC(윈도우)로는 포트가 포워딩되어 있지 않음.
* **해결**: `compose.yaml`에서 postgres와 redis 컨테이너에 `ports: - "5432:5432"`, `"6379:6379"` 설정을 추가하여 로컬에서 접근 가능하도록 개방함.

### 5. IntelliJ 빌드 시 'JWT_SECRET' Placeholder 에러
* **증상**: IDE에서 직접 앱 실행 시 `.env` 값을 읽어오지 못해 서버 크래시 발생.
* **원인**: IntelliJ 실행 시 Working Directory 기준점이 달라져 `application.properties`의 `../.env` 상대 경로를 찾지 못함.
* **해결**: 루트에 있던 `.env` 파일을 `be/` 폴더 안으로도 복사하고, `spring.config.import` 경로에 `optional:file:.env,optional:file:./.env`를 추가하여 어디서 실행하든 파일을 찾을 수 있게 보완함.

### 6. 인스타그램 리다이렉트 URI 및 Scope 불일치 에러
* **증상**: 계속해서 `Invalid redirect_uri` 에러 발생.
* **원인**: 백엔드에는 `http://...` 와 일반인 권한(`user_profile`)으로 세팅되었으나, 실제 Meta 앱은 HTTPS 연결과 비즈니스 권한(`instagram_business_basic` 등 5개)을 요구하도록 세팅됨.
* **해결**: `application.properties`의 리다이렉트 주소를 `https://`로 변경하고, 요청 `scope` 5가지를 Meta 대시보드와 완벽히 일치시킴.

### 7. 로컬 HTTPS 연결 거부 (ERR_CONNECTION_REFUSED)
* **증상**: 인스타그램이 로그인 성공 후 `https://localhost`로 돌려보냈으나 연결 거부됨.
* **원인**: 로컬 Nginx 서버가 80(HTTP) 포트만 열어두고 있었음.
* **해결**: OpenSSL을 이용해 사설(Self-signed) SSL 인증서를 생성하여 마운트하고, Nginx `default.conf`에서 443 포트(HTTPS)를 수신하도록 설정함.

### 8. OAuth2 Callback 시 404 및 /login?error 발생
* **증상**: 최종 콜백 과정에서 계속 에러 페이지로 튕김.
* **원인 1**: 테스트를 위해 인스타그램 URL을 브라우저에 직접 붙여넣어 진입함. (CSRF 방어용 `state` 값 누락) -> **반드시 백엔드 엔드포인트(`https://localhost/api/v1/users/instagram`)부터 시작해야 함.**
* **원인 2**: 인스타그램 API가 Access Token 응답 시 표준인 `token_type: "Bearer"`를 누락하여 Spring Security가 유효하지 않은 토큰으로 간주함 (`errorCode cannot be empty`).
* **해결**: `InstagramTokenResponseConverter` 커스텀 클래스를 생성하여 응답 토큰에 강제로 `Bearer` 타입을 주입하도록 `SecurityConfig` 설정을 오버라이딩함.

---

## 💡 주요 개념 정리

### 1. `expose`와 `ports`의 차이점 (Docker Compose)
도커(Docker) 컨테이너들을 **하나의 거대한 아파트 단지**라고 비유할 수 있습니다.
*   **`expose` (내선 전화)**: 기존 설정(`expose: "5432"`)은 아파트 단지 내부에서만 통하는 내선 전화를 개통한 것과 같습니다. 즉, 백엔드 컨테이너(101동)는 DB 컨테이너(102동)나 Redis 컨테이너(103동)에 자유롭게 연락할 수 있지만, **아파트 밖(사용자의 윈도우 컴퓨터나 IntelliJ 등)**에서는 전화를 걸 수 없습니다.
*   **`ports` (외부 직통 번호)**: 수정된 설정(`ports: "5432:5432"`)은 아파트 밖에서도 바로 걸 수 있는 외부 직통 번호를 뚫어준 것입니다. 사용자가 컴퓨터(로컬)에서 `build`나 `test`를 돌릴 때, 코드는 도커 컨테이너 안이 아니라 사용자의 컴퓨터(아파트 밖)에서 실행되므로, 외부에서 DB로 전화를 걸 수단(`ports`)이 반드시 필요합니다.

### 2. `JWT_SECRET`의 정체
`JWT_SECRET`은 인스타그램이나 페이스북 같은 외부에서 발급받아오는 API Key가 아닙니다.
백엔드 서버가 유저에게 주는 "우리 서비스 전용 자유이용권(Access Token/JWT)"이 진짜 우리 서버가 발급한 게 맞는지 구별할 수단이 필요한데, 이때 사용하는 **"도장(서명)"의 원본 비밀번호**가 바로 `JWT_SECRET`입니다.
우리 서버만이 이 비밀번호를 알고 있어야 토큰에 찍힌 도장이 진짜인지 판별할 수 있으며, 개발자가 영문/숫자/특수문자를 섞어서 32자 이상 마음대로 길게 만들어(`.env`에 저장하여) 사용하면 됩니다.

### 3. 유효한 OAuth 리디렉션 URI의 원리 (Meta 개발자 센터)
개발자 센터의 "유효한 OAuth 리디렉션 URI" 설정은 도착지를 하나로 고정하는 곳이 아니라, **"우리 앱이 허락해 주는 화이트리스트(허용 목록)"**입니다.
인스타그램 서버가 로그인 성공 후 유저를 어디로 돌려보낼지(Redirect) 결정하는 기준은 개발자 센터의 목록 순서가 아니라, **"애초에 백엔드 서버가 인스타그램에 접속할 때 꼬리표(`?redirect_uri=...`)로 뭐라고 요청했는가?"** 입니다.
여기에 `http://localhost/...`와 `http://k14a401.p.ssafy.io/...` 2개를 모두 등록해 두면, 로컬에서 실행할 때는 로컬로, 배포 서버에서 실행할 때는 배포 서버로 알아서 각각 돌아가게 되므로 두 환경을 충돌 없이 동시에 운영할 수 있습니다.

### 4. 도커 컨테이너에서 데이터베이스 직접 확인하기
*   **주의점**: `docker exec` 명령어는 컨테이너 안(Shell)에서 치는 것이 아니라, 윈도우 기본 터미널(로컬) 상태에서 도커 프로그램에게 명령을 내리는 것입니다. 컨테이너 내부 쉘(`root@...#`)에 이미 들어간 상태라면 `exit`을 입력해 빠져나와야 합니다.
*   **접속 및 확인 절차**:
    1.  컨테이너 내부 접속: `docker exec -it project-postgres bash`
    2.  PostgreSQL 실행: `psql -U myuser -d matketing_db`
    3.  테이블 목록 보기: `\dt`
    4.  데이터 조회: `SELECT * FROM users;`
    5.  Redis 확인(외부에서 한 줄로): `docker exec project-redis redis-cli -a myredispassword HGETALL refreshToken:유저ID`

### 5. 데이터베이스 스키마 관리 방식 (JPA vs ddl.sql)
*   **JPA 자동 생성 (`ddl-auto=update`)**: 자바 코드(`Entity` 클래스)의 모양만 바꿔주면, 스프링 서버가 켜질 때 알아서 데이터베이스 테이블을 만들거나 수정(DDL 자동 실행)해 주는 방식입니다. SQL을 몰라도 개발 속도가 엄청나게 빠르고 기획 변경에 대응하기 좋아 **개발 초기/프로토타입**에 최적입니다. 하지만 기존 데이터가 꼬이거나 날아갈 위험이 있어 예측 불가능하다는 단점이 있습니다.
*   **ddl.sql (스크립트 관리)**: 개발자가 직접 `CREATE TABLE ...` 같은 쿼리문 파일을 보관하고 실행하는 클래식한 방식입니다. 컴퓨터가 멋대로 DB를 건드리지 않아 완벽한 제어와 안정성을 보장하며, 변경 이력 추적이 가능합니다. 수동 작업이 번거롭지만 대형 사고를 막을 수 있어 실제 **서비스 출시/운영 단계**에서는 반드시 이 방식으로 전환해야 합니다.

### 6. InstagramTokenResponseConverter의 존재 이유 (Spring Security 커스텀)
전 세계 공통의 OAuth2 표준 규격에 따르면, 인증 서버는 토큰 발급 시 `token_type: "Bearer"` 항목을 반드시 포함하여 응답해야 합니다.
하지만 **인스타그램 API는 이 필수 항목을 쏙 빼먹고 반쪽짜리 토큰을 반환하는 고질적인 버그(또는 비표준 정책)**를 가지고 있습니다.
표준 규격을 엄격하게 지키는 Spring Security는 이 응답을 받자마자 유효하지 않은 토큰(`errorCode cannot be empty`)으로 간주하고 로그인 실패(`/login?error`) 처리를 냅니다.
이를 해결하기 위해 `InstagramTokenResponseConverter`라는 커스텀 클래스를 만들어, **인스타그램이 준 토큰 응답 사이에 백엔드가 강제로 `.tokenType(TokenType.BEARER)` 글자를 끼워 넣어 완벽한 규격으로 포장(심폐소생술)** 한 뒤 Spring Security에게 넘겨주도록 조치한 것입니다.

지금 be 안에도 .env가 있고 최상단에도 .env가 있는데 다 필요한거야?
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
✦ 아니요, 둘 다 "반드시" 필요한 것은 아닙니다! 사실 진짜 핵심은 최상단(루트)에 있는 .env 파일 딱 하나입니다.

그럼 왜 be 폴더 안에도 똑같은 .env 파일이 생겼는지, 그 이유를 아주 명쾌하게 설명해 드릴게요.

💡 왜 be 안에도 .env를 복사해 두었나요?
이건 오로지 사용자님이 IntelliJ(IDE)에서 녹색 재생 버튼(▶)을 눌러서 로컬 테스트를 편하게 하실 수 있도록 만든 임시방편(꼼수) 이었습니다.

1. Docker Compose로 실행할 때 (진짜 방식): 도커는 최상단 폴더에서 실행되기 때문에 루트에 있는 .env 파일 하나만 보고도 백엔드(spring), 데이터베이스(postgres) 등에 환경
   변수를 아주 잘 나눠줍니다.
2. IntelliJ에서 실행할 때 (문제 발생): IntelliJ에서 백엔드 앱(BeApplication)을 단독으로 실행하면, 실행 기준점(Working Directory)이 루트 폴더가 아니라 be 폴더 내부로
   잡히는 경우가 많습니다. 그래서 스프링 서버가 켜질 때 한 칸 위에 있는 ../.env를 찾지 못하고 길을 잃어버려서 에러(JWT_SECRET 없음)를 뱉었었죠.

그래서 "IntelliJ가 헷갈리지 않게, 아예 네가 실행되는 바로 그 폴더(be/) 안에도 똑같은 파일을 하나 복사해 줄게!" 하고 넣어둔 것입니다.

  ---

🚀 결론 및 관리 방법

* 실제 배포 서버(운영 환경)에 올리실 때는: 최상단 루트 폴더에 있는 .env 파일 단 1개만 있으면 완벽하게 작동합니다. (Docker Compose를 쓸 것이기 때문입니다.)
* Git(깃) 저장소에 올리실 때는: .env 파일에는 인스타그램 시크릿 키, DB 비밀번호 같은 민감한 정보가 들어있으므로 루트에 있는 것이든 be 안에 있는 것이든 절대 깃허브에
  올리시면 안 됩니다! (다행히 .gitignore에 잘 등록되어 있을 것입니다.)
* 로컬 개발하실 때는: 루트에 있는 .env를 메인으로 관리하시되, 변수 값이 바뀌면 잊지 말고 be/.env 에도 복사/붙여넣기를 해주셔야 IntelliJ에서 실행할 때 에러가 나지
  않습니다.

나중에 IntelliJ의 실행 설정(Run Configuration)에서 "Working Directory"를 프로젝트 루트로 수동 고정해 주시면, be/.env 파일은 미련 없이 지워버리셔도 됩니다!


✦ 아, 맞습니다! 제 생각이 짧았습니다. 로컬 테스트 따로, 배포 환경 따로 일일이 수정하는 것은 정말 불편하죠.

사용자님이 제안해주신 그 완벽한 구조(로컬에서는 .env.local 자동 적용, 배포에서는 .env 적용) 대로 설정을 다시 롤백하고 깔끔하게 셋팅해 두었습니다!

🛠️ 어떻게 구현했나요?
Docker Compose의 강력한 기능인 다중 env_file 오버라이딩(덮어쓰기) 기능을 사용했습니다.

compose.yaml 파일의 spring 컨테이너 설정을 아래와 같이 수정했습니다.

1     env_file:
2       - path: .env           # 1. 먼저 루트의 .env(배포용)를 읽어옵니다. (필수)
3         required: true
4       - path: be/.env.local  # 2. 그 다음 be/.env.local(로컬용)이 있다면 읽어서 덮어씌웁니다! (선택)
5         required: false

✨ 이제 얻게 된 장점!
* [로컬 개발 시]
    - 로컬 컴퓨터에는 be/.env.local 파일이 존재하므로, 도커가 배포용 주소(k14a401...)를 먼저 읽었다가 곧바로 로컬 주소(localhost)로 덮어써 버립니다.
    - 방금 제가 테스트해 본 결과, 꼬리표(redirect_uri)가 로컬 주소로 완벽하게 잘 나오는 것을 확인했습니다!
    - 👉 https://localhost/api/v1/users/instagram
* [배포 서버 시]
    - 배포 서버(Ubuntu 등)나 Git 저장소에는 be/.env.local 파일을 올리지 않으실 테니, 서버에는 해당 파일이 존재하지 않습니다.
    - 도커가 .env.local을 찾다가 "어라, 없네? 그럼 무시하자" 하고 넘어가기 때문에, 처음에 읽었던 루트 .env 안의 배포 주소(k14a401...)가 그대로 적용됩니다.
    - 👉 http://k14a401.p.ssafy.io/api/v1/users/instagram

이로써 코드나 설정 파일을 단 1바이트도 수정하지 않고, 로컬 환경과 배포 서버 환경을 100% 자동으로 스위칭 할 수 있는 이상적인 아키텍처가 완성되었습니다! 정말 예리한
지적이셨습니다. 👍
