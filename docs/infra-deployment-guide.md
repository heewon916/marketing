# 인프라 배포 운영 가이드

이 문서는 현재 Jenkins, Docker Compose, Nginx, Spring, FastAPI, Frontend 배포가 어떻게 동작하는지 팀원이 빠르게 파악할 수 있도록 정리한 운영 가이드입니다.

## 전체 구조

현재 배포는 Jenkins가 GitLab 저장소를 checkout한 뒤, 배포 서버의 `/home/ubuntu/deploy/S14P31A401` 디렉터리에 소스를 복사하고 Docker Compose로 컨테이너를 빌드/실행하는 방식입니다.

```text
GitLab develop
  -> Jenkins develop-deploy job
  -> /home/ubuntu/deploy/S14P31A401
  -> docker compose
  -> nginx, frontend, spring, fastapi, postgres, redis
```

외부 요청 흐름은 다음과 같습니다.

```text
사용자
  -> nginx:80/443
    -> frontend
    -> spring API
    -> fastapi AI API
```

## 주요 파일

- `common/Jenkinsfile`: Jenkins 배포 파이프라인
- `compose.yaml`: Docker Compose 서비스 정의
- `nginx/Dockerfile`: Nginx 이미지 빌드
- `nginx/conf.d/default.conf`: Nginx reverse proxy 설정
- `be/Dockerfile`: Spring Boot 이미지 빌드
- `fe/Dockerfile`: Frontend 빌드 후 Nginx로 정적 파일 서빙
- `ai/Dockerfile`: FastAPI 이미지 빌드

## Jenkins Credentials

Jenkins의 `System > Global credentials`에 아래 credentials가 필요합니다.

### GitLab Repository Credential

```text
ID: gitlab-repo-credential
Kind: Username with password
Purpose: Jenkins가 GitLab 저장소를 clone/fetch 할 때 사용
```

### GitLab API Token

```text
ID: gitlab-api-token
Kind: GitLab API token
Purpose: Jenkins GitLab 플러그인이 GitLab API와 통신할 때 사용
```

### Environment File

```text
ID: marketing-env-file
Kind: Secret file
File name: .env 또는 marketing-env-file.env
Purpose: 배포 환경변수 파일
```

`marketing-env-file`에는 다음 key가 필요합니다.

```env
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
REDIS_PASSWORD=

S3_BUCKET_NAME=
S3_REGION=
S3_ACCESS_KEY=
S3_SECRET_KEY=
CLOUDFRONT_DOMAIN=

VITE_KAKAO_MAP_KEY=
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_FIREBASE_MEASUREMENT_ID=
VITE_FIREBASE_VAPID_KEY=
VITE_API_BACKEND_URL=

JWT_SECRET=
OAUTH_REDIRECT_URI=
FRONTEND_URL=
INSTAGRAM_CLIENT_ID=
INSTAGRAM_CLIENT_SECRET=

FIREBASE_ENABLED=true
```

`VITE_FIREBASE_MEASUREMENT_ID` 철자를 맞춰야 합니다. `MEASUREMET`처럼 오타가 있으면 Jenkins env 검증에서 실패합니다.

### Firebase Service Account

```text
ID: marketing-firebase-service-account-file
Kind: Secret file
File name: firebase-service-account.json
Purpose: Firebase Admin SDK service account JSON
```

이 파일은 Git에 커밋하지 않습니다. Jenkins가 배포 시 다음 경로로 복사합니다.

```text
/home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
```

Spring 컨테이너 내부에서는 다음 경로로 읽습니다.

```text
file:/run/secrets/firebase-service-account.json
```

## Jenkins 배포 흐름

### 1. Checkout

Jenkins가 `gitlab-repo-credential`로 GitLab 저장소를 checkout합니다.

### 2. 변경 서비스 감지

`common/Jenkinsfile`은 이전 성공 커밋과 현재 커밋의 diff를 비교해서 빌드할 서비스를 결정합니다.

```text
be/**      -> spring
fe/**      -> frontend
ai/**      -> fastapi
nginx/**   -> nginx
compose.yaml 또는 common/Jenkinsfile -> 전체 애플리케이션 이미지
```

변경 서비스 목록은 `.build-services` 파일에 저장됩니다.

### 3. 배포 디렉터리 준비

Jenkins workspace를 `/home/ubuntu/deploy/S14P31A401`로 복사합니다.

복사에서 제외되는 항목:

- `.git`
- `node_modules`
- `dist`
- `build`
- `.gradle`
- `.pnpm-store`
- `.env`
- `secrets`
- `be/src/main/resources/firebase/firebase-service-account.json`

비밀 파일이 workspace에 있어도 배포 디렉터리로 섞이지 않게 하기 위한 처리입니다.

### 4. Secret 준비

Jenkins Secret file에서 `.env`를 복사합니다.

```text
marketing-env-file -> /home/ubuntu/deploy/S14P31A401/.env
```

Firebase service account JSON도 복사합니다.

```text
marketing-firebase-service-account-file
  -> /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
```

두 파일 모두 Jenkins 로그에 내용이 출력되지 않습니다.

### 5. Env 검증

Jenkins는 `.env`의 key만 출력하고 값은 출력하지 않습니다.

검증 항목:

- 필수 key 존재 여부
- 빈 값 여부
- placeholder 값 여부
- CRLF 포함 여부
- 중복 key 여부
- `S3_REGION` 형식
- `CLOUDFRONT_DOMAIN` 형식
- `FIREBASE_ENABLED`가 `true` 또는 `false`인지

### 6. Compose 검증

`docker compose config`는 env 값을 펼쳐 출력할 수 있으므로 stdout을 막고 성공 여부만 남깁니다.

```sh
docker compose -p marketing -f compose.yaml --env-file .env config >/dev/null
```

### 7. 이미지 빌드와 컨테이너 교체

변경된 서비스만 빌드합니다.

```sh
docker compose -p marketing -f compose.yaml --env-file .env build $BUILD_SERVICES
```

이후 DB/Redis를 먼저 보장하고, 변경된 애플리케이션 서비스만 재생성합니다.

```sh
docker compose -p marketing -f compose.yaml --env-file .env up -d postgres redis
docker compose -p marketing -f compose.yaml --env-file .env up -d --no-deps --force-recreate $BUILD_SERVICES
docker compose -p marketing -f compose.yaml --env-file .env up -d --remove-orphans
```

## 이미지 Revision 확인

각 Docker 이미지에는 빌드된 Git commit SHA가 label로 들어갑니다.

```dockerfile
ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.revision=$BUILD_COMMIT
```

배포 후 Jenkins 로그에 컨테이너별 revision이 출력됩니다.

```text
spring=<commit-sha>
frontend=<commit-sha>
nginx=<commit-sha>
fastapi=<commit-sha>
```

이 값으로 실제 떠 있는 컨테이너가 어떤 커밋으로 빌드됐는지 확인할 수 있습니다.

## 서비스별 환경변수 전달 방식

### Spring

Spring은 런타임 환경변수로 값을 받습니다.

주요 값:

- DB/Redis 접속 정보
- S3/CloudFront 정보
- JWT secret
- Instagram OAuth 정보
- Firebase 설정

Firebase는 운영에서 secret file mount를 사용합니다.

```yaml
volumes:
  - ./secrets/firebase-service-account.json:/run/secrets/firebase-service-account.json:ro
```

### Frontend

Vite의 `VITE_*` 값은 런타임이 아니라 빌드 타임에 정적 파일에 포함됩니다.

따라서 `compose.yaml`의 build args와 `fe/Dockerfile`의 `ARG`/`ENV`를 통해 `pnpm build` 전에 주입합니다.

Frontend env만 바꾼 경우에는 기존 정적 빌드 결과가 자동으로 바뀌지 않습니다. frontend 이미지를 다시 빌드해야 반영됩니다.

### FastAPI

FastAPI는 런타임 환경변수로 S3/CloudFront 값을 받습니다.

AI 의존성 설치는 무겁기 때문에 `ai/pyproject.toml`, `ai/uv.lock`, `ai/Dockerfile` 변경 시 빌드 시간이 길어질 수 있습니다.

## Nginx 인증서

Nginx 인증서는 Docker 이미지에 복사하지 않습니다.

운영 서버의 Let's Encrypt 경로를 컨테이너에 read-only로 마운트합니다.

```yaml
volumes:
  - /etc/letsencrypt:/etc/letsencrypt:ro
```

따라서 `nginx/certs` 디렉터리는 필요하지 않습니다. 인증서를 이미지에 포함하면 인증서가 Docker image layer에 남고, 갱신 때마다 이미지를 다시 빌드해야 하므로 운영에 적합하지 않습니다.

## Secret 로그 노출 주의사항

Jenkinsfile에서는 secret 값을 직접 출력하지 않아야 합니다.

금지 예시:

```sh
cat .env
env
printenv
docker compose config
docker inspect project-spring
```

허용 예시:

```sh
# key만 출력
awk -F= '{ print $1 }' .env

# compose 검증 결과만 확인
docker compose config >/dev/null

# revision label만 출력
docker inspect project-spring --format 'spring={{ index .Config.Labels "org.opencontainers.image.revision" }}'
```

## 배포 후 확인

Jenkins 배포가 끝나면 다음 단계가 통과해야 합니다.

- `Check Docker`
- `Validate Compose`
- `Deploy`
- `Check Nginx Config`
- `Health Check`

Health check는 Nginx 네트워크를 통해 다음 경로를 확인합니다.

```text
http://nginx
http://nginx/api/health
http://nginx/api/ai-health
```

## 자주 발생하는 문제

장애가 발생했을 때의 구체적인 확인 순서는 `docs/infra-troubleshooting-checklist.md`를 참고합니다.

### Jenkins가 credential을 찾지 못함

Jenkins credential ID가 정확한지 확인합니다.

```text
marketing-env-file
marketing-firebase-service-account-file
gitlab-repo-credential
gitlab-api-token
```

### `.env` 검증 실패

Jenkins 로그의 `.env keys only`에서 누락된 key를 확인합니다. 값은 로그에 출력되지 않습니다.

### Firebase secret 파일 없음

`marketing-firebase-service-account-file`이 Secret file로 등록되어 있는지 확인합니다.

### Nginx 빌드에서 certs 복사 실패

현재 구조에서는 `nginx/certs`를 이미지에 복사하지 않습니다. 인증서는 `/etc/letsencrypt` volume mount로 제공합니다.

### AI 빌드가 너무 오래 걸림

AI 의존성 설치가 무겁기 때문입니다. 일반적으로 `ai/**`가 변경되지 않으면 AI 이미지는 다시 빌드되지 않습니다. `compose.yaml` 또는 `common/Jenkinsfile` 변경 시에는 전체 빌드가 잡혀 AI도 빌드될 수 있습니다.
