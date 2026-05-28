# 인프라 코드 설명서

이 문서는 현재 저장소에서 배포, 컨테이너 실행, 프록시, 런타임 환경변수와 직접 관련된 파일들이 어떤 의미를 가지는지 정리한 문서입니다.

## 전체 구성 요약

현재 인프라는 Docker Compose 기반으로 여러 서비스를 하나의 Docker 네트워크에 묶어 실행합니다.

- `nginx`: 외부 HTTP/HTTPS 요청을 받는 리버스 프록시입니다.
- `frontend`: React/Vite 빌드 결과물을 Nginx로 서빙하는 프론트엔드 컨테이너입니다.
- `spring`: Spring Boot 백엔드 API 컨테이너입니다.
- `fastapi`: Python FastAPI 기반 AI 서비스 컨테이너입니다.
- `postgres`: PostgreSQL + pgvector 데이터베이스 컨테이너입니다.
- `redis`: Redis 캐시/세션 저장소 컨테이너입니다.
- `common/Jenkinsfile`: Jenkins에서 서버 배포를 자동화하는 파이프라인입니다.

요청 흐름은 대략 다음과 같습니다.

```text
사용자 브라우저
  -> Nginx(80/443)
    -> /           -> frontend
    -> /api/       -> spring
    -> /ai/        -> fastapi
    -> /ai/docs    -> fastapi Swagger UI
```

## `compose.yaml`

Docker Compose가 전체 서비스를 정의하는 핵심 파일입니다.

### `services`

여러 컨테이너 서비스를 선언하는 최상위 블록입니다.

### `nginx`

```yaml
nginx:
  build:
    context: ./nginx
    dockerfile: Dockerfile
```

- `./nginx` 디렉터리를 빌드 컨텍스트로 사용합니다.
- `nginx/Dockerfile`로 Nginx 이미지를 만듭니다.

```yaml
container_name: project-nginx
restart: unless-stopped
```

- 컨테이너 이름을 `project-nginx`로 고정합니다.
- 사용자가 직접 중지하지 않는 한 장애나 서버 재시작 후 다시 실행됩니다.

```yaml
ports:
  - "80:80"
  - "443:443"
```

- 서버의 80번 포트를 컨테이너의 80번 포트에 연결합니다.
- 서버의 443번 포트를 컨테이너의 443번 포트에 연결합니다.
- 즉 외부 사용자는 HTTP/HTTPS로 Nginx에 접근합니다.

```yaml
volumes:
  - /etc/letsencrypt:/etc/letsencrypt:ro
```

- 서버의 Let's Encrypt 인증서 디렉터리를 Nginx 컨테이너에 읽기 전용으로 마운트합니다.
- `:ro`는 컨테이너가 인증서를 수정하지 못하게 하는 옵션입니다.

```yaml
depends_on:
  - spring
  - frontend
```

- `nginx`가 `spring`, `frontend`보다 나중에 생성되도록 합니다.
- 단, 서비스가 완전히 준비될 때까지 기다리는 기능은 아닙니다.

```yaml
networks:
  - project-network
```

- 같은 네트워크에 있는 컨테이너끼리 서비스 이름으로 통신할 수 있게 합니다.
- 예를 들어 Nginx 설정에서 `http://spring:8080`처럼 접근할 수 있습니다.

### `spring`

Spring Boot 백엔드 API 서비스입니다.

```yaml
build:
  context: ./be
  dockerfile: Dockerfile
image: marketing-spring:latest
```

- `be/Dockerfile`로 이미지를 빌드합니다.
- 빌드된 이미지 이름은 `marketing-spring:latest`입니다.

```yaml
env_file:
  - .env
```

- 루트의 `.env` 파일을 컨테이너 환경변수로 주입합니다.
- `.env`는 Git에 올리지 않는 비밀 설정 파일입니다.

```yaml
environment:
  FASTAPI_BASE_URL: http://fastapi:8000
  SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/${POSTGRES_DB}
  SPRING_DATASOURCE_USERNAME: ${POSTGRES_USER}
  SPRING_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD}
  SPRING_DATA_REDIS_HOST: redis
  SPRING_DATA_REDIS_PORT: 6379
  SPRING_DATA_REDIS_PASSWORD: ${REDIS_PASSWORD}
```

- Spring 컨테이너 안에서 사용할 환경변수를 명시합니다.
- `postgres`, `redis`, `fastapi`는 Docker Compose 네트워크의 서비스 이름입니다.
- `${POSTGRES_DB}` 같은 값은 `.env`에서 가져옵니다.
- Spring Boot는 `SPRING_DATASOURCE_URL` 같은 환경변수를 `spring.datasource.url` 설정으로 인식합니다.

```yaml
S3_BUCKET_NAME: ${S3_BUCKET_NAME}
S3_REGION: ${S3_REGION}
CLOUDFRONT_DOMAIN: ${CLOUDFRONT_DOMAIN}
S3_ACCESS_KEY: ${S3_ACCESS_KEY}
S3_SECRET_KEY: ${S3_SECRET_KEY}
```

- 이미지/파일 업로드, CDN URL 생성 등에 필요한 AWS S3 및 CloudFront 설정입니다.

```yaml
expose:
  - "8080"
```

- Compose 내부 네트워크에서 8080 포트를 노출합니다.
- 외부 서버 포트로 직접 공개하는 `ports`와 다릅니다.
- 외부 사용자는 Spring에 직접 접근하지 않고 Nginx를 통해 접근합니다.

```yaml
depends_on:
  - fastapi
  - postgres
  - redis
```

- Spring 컨테이너가 AI 서비스, DB, Redis 컨테이너 생성 후 올라오도록 합니다.

### `frontend`

React/Vite 프론트엔드 서비스입니다.

```yaml
build:
  context: ./fe
  dockerfile: Dockerfile
image: marketing-frontend:latest
```

- `fe/Dockerfile`로 프론트엔드 정적 파일을 빌드하고 Nginx 이미지로 서빙합니다.

```yaml
expose:
  - "80"
```

- 내부 네트워크에서만 80번 포트를 노출합니다.
- 외부 사용자는 `project-nginx` 컨테이너를 통해 접근합니다.

### `postgres`

PostgreSQL 데이터베이스 서비스입니다.

```yaml
image: pgvector/pgvector:pg16
```

- PostgreSQL 16 기반에 pgvector 확장이 포함된 이미지를 사용합니다.
- 벡터 검색이나 임베딩 저장이 필요한 경우 사용할 수 있습니다.

```yaml
ports:
  - "127.0.0.1:5432:5432"
```

- 서버 자기 자신의 `127.0.0.1:5432`에만 DB 포트를 엽니다.
- 외부 인터넷에는 직접 노출하지 않습니다.
- 서버 내부에서만 DB 클라이언트로 접속할 수 있습니다.

```yaml
environment:
  POSTGRES_DB: ${POSTGRES_DB}
  POSTGRES_USER: ${POSTGRES_USER}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

- DB 이름, 사용자, 비밀번호를 `.env`에서 가져옵니다.

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

- DB 데이터를 Docker 볼륨에 저장합니다.
- 컨테이너를 재생성해도 데이터가 유지됩니다.

### `redis`

Redis 서비스입니다.

```yaml
image: redis:8.4.0
```

- Redis 8.4.0 이미지를 사용합니다.

```yaml
command:
  - redis-server
  - --requirepass
  - ${REDIS_PASSWORD}
  - --appendonly
  - "yes"
```

- Redis 서버를 비밀번호 필수 모드로 실행합니다.
- `--appendonly yes`는 AOF 영속화를 켜서 Redis 데이터를 디스크에도 기록합니다.

```yaml
volumes:
  - redis_data:/data
```

- Redis 영속화 파일을 Docker 볼륨에 저장합니다.

### `fastapi`

AI 기능을 제공하는 Python FastAPI 서비스입니다.

```yaml
build:
  context: ./ai
  dockerfile: Dockerfile
image: marketing-fastapi:latest
```

- `ai/Dockerfile`로 FastAPI 이미지를 빌드합니다.

```yaml
environment:
  S3_BUCKET_NAME: ${S3_BUCKET_NAME}
  S3_REGION: ${S3_REGION}
  S3_ACCESS_KEY: ${S3_ACCESS_KEY}
  S3_SECRET_KEY: ${S3_SECRET_KEY}
  CLOUDFRONT_DOMAIN: ${CLOUDFRONT_DOMAIN}
  KEYWORD_MODEL_GPU_LAYERS: "0"
```

- AI 서비스가 S3/CloudFront 설정을 사용하도록 환경변수를 전달합니다.
- `KEYWORD_MODEL_GPU_LAYERS: "0"`은 키워드 모델을 GPU 레이어 없이 CPU 중심으로 실행하겠다는 설정입니다.

```yaml
expose:
  - "8000"
```

- FastAPI의 8000번 포트를 Compose 내부 네트워크에 노출합니다.

### `volumes`

```yaml
volumes:
  postgres_data:
  redis_data:
```

- Compose가 관리하는 영구 저장소입니다.
- DB와 Redis 데이터가 컨테이너 생명주기와 분리되어 유지됩니다.

### `networks`

```yaml
networks:
  project-network:
    driver: bridge
```

- 서비스들을 하나의 브리지 네트워크로 묶습니다.
- 같은 네트워크 안에서는 서비스 이름이 DNS 이름처럼 동작합니다.

## `nginx/Dockerfile`

Nginx 리버스 프록시 이미지를 만드는 파일입니다.

```dockerfile
FROM nginx:1.27-alpine
```

- Alpine Linux 기반의 가벼운 Nginx 1.27 이미지를 사용합니다.

```dockerfile
RUN rm -f /etc/nginx/conf.d/default.conf
```

- 기본 Nginx 설정 파일을 삭제합니다.
- 기본 설정과 커스텀 설정이 충돌하지 않도록 하기 위한 작업입니다.

```dockerfile
COPY conf.d /etc/nginx/conf.d
```

- 저장소의 `nginx/conf.d` 디렉터리를 컨테이너의 Nginx 설정 디렉터리로 복사합니다.
- 결과적으로 `nginx/conf.d/default.conf`가 실제 서버 설정으로 사용됩니다.

## `nginx/conf.d/default.conf`

외부 요청을 받아 프론트엔드, Spring, FastAPI로 나누어 전달하는 Nginx 설정입니다.

### HTTP 서버 블록

```nginx
server {
    listen 80;
    server_name maketing.co.kr www.maketing.co.kr;

    return 301 https://www.maketing.co.kr$request_uri;
}
```

- 80번 HTTP 요청을 받습니다.
- 도메인은 `maketing.co.kr`, `www.maketing.co.kr`입니다.
- 모든 HTTP 요청을 `https://www.maketing.co.kr`로 301 리다이렉트합니다.
- `$request_uri`는 기존 경로와 쿼리스트링을 유지합니다.

### HTTPS 서버 블록

```nginx
server {
    listen 443 ssl;
    server_name maketing.co.kr www.maketing.co.kr;
```

- 443번 HTTPS 요청을 받습니다.
- SSL/TLS를 사용합니다.

```nginx
ssl_certificate /etc/letsencrypt/live/maketing.co.kr/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/maketing.co.kr/privkey.pem;
```

- Let's Encrypt 인증서와 개인키 경로입니다.
- 이 경로는 `compose.yaml`에서 `/etc/letsencrypt`를 마운트했기 때문에 컨테이너 안에서도 접근 가능합니다.

### `/api/`

```nginx
location /api/ {
    proxy_pass http://spring:8080/api/;
```

- `/api/`로 시작하는 요청을 Spring 컨테이너의 8080 포트로 전달합니다.
- 예를 들어 `/api/health`는 `http://spring:8080/api/health`로 전달됩니다.

```nginx
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

- 백엔드가 원래 요청의 도메인, 클라이언트 IP, 프로토콜을 알 수 있도록 헤더를 전달합니다.
- `X-Forwarded-Proto`는 Spring에서 HTTPS 여부를 판단할 때 중요합니다.

```nginx
proxy_connect_timeout 300;
proxy_send_timeout 300;
proxy_read_timeout 300;
```

- AI 처리나 파일 처리처럼 오래 걸리는 API를 고려해 프록시 타임아웃을 300초로 늘린 설정입니다.

### `/ai/docs`

```nginx
location = /ai/docs {
    proxy_pass http://fastapi:8000/docs;
}
```

- 정확히 `/ai/docs` 요청만 FastAPI의 Swagger UI인 `/docs`로 전달합니다.
- `=`는 정확히 일치하는 경로만 매칭한다는 뜻입니다.

### `/ai/openapi.json`

```nginx
location = /ai/openapi.json {
    proxy_pass http://fastapi:8000/ai/openapi.json;
}
```

- FastAPI OpenAPI JSON 문서 요청을 전달합니다.
- Swagger UI가 API 명세를 읽을 때 필요합니다.

### `/ai/`

```nginx
location /ai/ {
    proxy_pass http://fastapi:8000/ai/;
}
```

- `/ai/`로 시작하는 일반 AI API 요청을 FastAPI로 전달합니다.

### `/`

```nginx
location / {
    proxy_pass http://frontend:80;
    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
}
```

- 위 API 경로에 해당하지 않는 모든 요청을 프론트엔드로 보냅니다.
- 캐시를 막는 헤더를 추가해 새 배포 후 오래된 프론트엔드 파일이 남는 문제를 줄입니다.

## `be/Dockerfile`

Spring Boot 백엔드 이미지를 만드는 Dockerfile입니다.

```dockerfile
FROM eclipse-temurin:21-jdk AS build
```

- Java 21 JDK 이미지로 빌드 단계를 시작합니다.
- `AS build`는 멀티 스테이지 빌드의 첫 번째 단계 이름입니다.

```dockerfile
WORKDIR /app
COPY . .
```

- 컨테이너 내부 작업 디렉터리를 `/app`으로 설정합니다.
- 백엔드 소스 전체를 `/app`으로 복사합니다.

```dockerfile
RUN chmod +x ./gradlew
RUN ./gradlew clean bootJar -x test
```

- Gradle Wrapper 실행 권한을 부여합니다.
- 테스트를 제외하고 Spring Boot 실행 JAR를 빌드합니다.
- `-x test`는 Docker 이미지 빌드 시간을 줄이지만, 배포 전 별도 테스트가 없다면 결함을 놓칠 수 있습니다.

```dockerfile
FROM eclipse-temurin:21-jre
WORKDIR /app
```

- 실행 단계에서는 JDK보다 가벼운 JRE 이미지를 사용합니다.

```dockerfile
COPY --from=build /app/build/libs/*.jar app.jar
```

- 빌드 단계에서 생성된 JAR 파일만 실행 이미지로 복사합니다.
- 소스코드나 Gradle 캐시는 최종 이미지에 포함하지 않습니다.

```dockerfile
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

- 컨테이너가 8080 포트를 사용한다는 정보를 남깁니다.
- 컨테이너 시작 시 `java -jar app.jar`로 Spring Boot 앱을 실행합니다.

## `fe/Dockerfile`

프론트엔드를 빌드하고 정적 파일을 Nginx로 서빙하는 Dockerfile입니다.

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
```

- Node.js 22 Alpine 이미지로 빌드 단계를 시작합니다.

```dockerfile
RUN npm install -g pnpm
```

- 패키지 매니저 `pnpm`을 전역 설치합니다.

```dockerfile
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
```

- 의존성 명세 파일만 먼저 복사한 뒤 의존성을 설치합니다.
- `--frozen-lockfile`은 lockfile과 실제 설치 결과가 달라지지 않도록 보장합니다.
- Docker 캐시를 효율적으로 쓰기 위해 소스 전체 복사보다 의존성 설치를 먼저 합니다.

```dockerfile
COPY . .
RUN pnpm build
```

- 프론트엔드 소스 전체를 복사하고 프로덕션 빌드를 수행합니다.
- 결과물은 일반적으로 `/app/dist`에 생성됩니다.

```dockerfile
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

- 실행 이미지는 Nginx입니다.
- 빌드된 정적 파일을 Nginx 기본 정적 파일 경로로 복사합니다.

```dockerfile
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

- 80번 포트를 사용합니다.
- Nginx를 포그라운드로 실행해 컨테이너가 종료되지 않게 합니다.

## `ai/Dockerfile`

FastAPI AI 서비스 이미지를 만드는 Dockerfile입니다.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
```

- Python 3.12 slim 이미지를 사용합니다.
- 작업 디렉터리는 `/app`입니다.

```dockerfile
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"
```

- `uv` 패키지 설치 방식과 Python bytecode 컴파일 옵션을 설정합니다.
- `CMAKE_ARGS`는 llama.cpp 계열 패키지 빌드 시 OpenBLAS를 사용하도록 하는 옵션입니다.

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        pkg-config \
        libopenblas-dev \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*
```

- Python 패키지 중 네이티브 컴파일이 필요한 의존성을 위해 빌드 도구와 OpenBLAS 라이브러리를 설치합니다.
- 마지막 줄은 apt 캐시를 지워 이미지 크기를 줄입니다.

```dockerfile
RUN pip install --no-cache-dir uv
```

- Python 패키지 매니저 `uv`를 설치합니다.

```dockerfile
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
```

- 의존성 파일을 먼저 복사하고 프로덕션 의존성만 설치합니다.
- `--frozen`은 lockfile 기준으로만 설치한다는 뜻입니다.
- `--no-dev`는 개발 의존성을 제외합니다.
- `--no-install-project`는 아직 소스가 복사되지 않은 상태에서 프로젝트 자체 설치는 건너뜁니다.

```dockerfile
COPY . .
RUN uv sync --frozen --no-dev
```

- 전체 소스를 복사한 뒤 프로젝트까지 포함해 의존성 동기화를 완료합니다.

```dockerfile
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- FastAPI가 8000번 포트로 실행됩니다.
- `--host 0.0.0.0`은 컨테이너 외부에서 접근 가능하게 바인딩한다는 의미입니다.
- Compose 내부에서는 `http://fastapi:8000`으로 접근합니다.

## `common/Jenkinsfile`

Jenkins가 배포 서버에서 코드를 복사하고 Docker Compose로 서비스를 배포하는 파이프라인입니다.

### 최상위 설정

```groovy
pipeline {
    agent any
```

- Jenkins Declarative Pipeline 문법입니다.
- 사용 가능한 아무 Jenkins agent에서나 실행됩니다.

```groovy
environment {
    DEPLOY_DIR = '/home/ubuntu/deploy/S14P31A401'
    COMPOSE_FILE = 'compose.yaml'
    PROJECT_NAME = 'marketing'
}
```

- 배포 디렉터리, Compose 파일명, Compose 프로젝트 이름을 전역 환경변수로 둡니다.
- Compose 프로젝트 이름은 네트워크와 볼륨 이름의 prefix에 영향을 줍니다.

### `Checkout Info`

```groovy
stage('Checkout Info') {
    steps {
        sh '''
            pwd
            ls -al
            git branch -a || true
        '''
    }
}
```

- 현재 Jenkins 작업 디렉터리, 파일 목록, 브랜치 정보를 출력합니다.
- 배포 실패 시 어떤 코드가 배포 대상이었는지 확인하기 위한 진단 단계입니다.

### `Prepare Deploy Directory`

```groovy
mkdir -p "${DEPLOY_DIR}"
rm -rf "${DEPLOY_DIR:?}/"* "${DEPLOY_DIR}"/.[!.]* "${DEPLOY_DIR}"/..?* 2>/dev/null || true
```

- 배포 디렉터리를 생성합니다.
- 기존 배포 디렉터리의 내용을 삭제합니다.
- `${DEPLOY_DIR:?}`는 변수가 비어 있을 때 명령 실행을 막아 위험한 삭제를 줄입니다.

```groovy
tar \
  --exclude='./.git' \
  --exclude='*/node_modules' \
  --exclude='*/dist' \
  --exclude='*/build' \
  --exclude='*/.gradle' \
  --exclude='*/.pnpm-store' \
  --exclude='./.env' \
  -cf - . | tar -C "${DEPLOY_DIR}" -xf -
```

- Jenkins workspace의 파일을 배포 디렉터리로 복사합니다.
- `.git`, 빌드 산출물, 의존성 디렉터리, `.env`는 제외합니다.
- `.env`는 Jenkins Secret File에서 따로 주입합니다.

### `Prepare Env`

```groovy
withCredentials([file(credentialsId: 'marketing-env-file', variable: 'ENV_FILE_PATH')]) {
```

- Jenkins Credentials에 저장된 Secret File을 임시 파일 경로로 받아옵니다.
- credential ID는 `marketing-env-file`입니다.

```groovy
cp "$ENV_FILE_PATH" "${DEPLOY_DIR}/.env"
sed -i 's/\r$//' "${DEPLOY_DIR}/.env"
chmod 600 "${DEPLOY_DIR}/.env"
```

- Secret File을 배포 디렉터리의 `.env`로 복사합니다.
- Windows CRLF 줄바꿈을 LF로 정리합니다.
- 권한을 `600`으로 제한해 소유자만 읽고 쓸 수 있게 합니다.

### `Validate Env`

`.env`가 배포에 필요한 값을 제대로 가지고 있는지 검사합니다.

```groovy
test -s "$ENV_PATH"
```

- `.env` 파일이 존재하고 비어 있지 않은지 확인합니다.

```groovy
awk -F= '...' "$ENV_PATH"
```

- `.env`의 key 목록만 출력합니다.
- secret value는 로그에 남기지 않습니다.

```groovy
if grep -q "$(printf '\r')" "$ENV_PATH"; then
```

- CRLF 줄바꿈이 남아 있으면 배포를 중단합니다.

```groovy
DUP_KEYS=$(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_PATH" | cut -d= -f1 | sort | uniq -d || true)
```

- 중복된 환경변수 key가 있는지 검사합니다.

```groovy
require_env POSTGRES_DB
require_env POSTGRES_USER
require_env POSTGRES_PASSWORD
require_env REDIS_PASSWORD
require_env S3_BUCKET_NAME
require_env S3_REGION
require_env S3_ACCESS_KEY
require_env S3_SECRET_KEY
require_env CLOUDFRONT_DOMAIN
```

- 필수 환경변수가 없거나 비어 있으면 배포를 중단합니다.
- `changeme`, `TODO`, `undefined` 같은 placeholder 값도 금지합니다.

```groovy
echo "$S3_REGION_VALUE" | grep -Eq '^[a-z]{2}-[a-z]+-[0-9]+$'
```

- AWS region 형식이 대략 `ap-northeast-2` 같은 형태인지 검사합니다.

```groovy
echo "$CLOUDFRONT_DOMAIN_VALUE" | grep -Eq '^https?://' && ...
```

- CloudFront 도메인에 `http://` 또는 `https://`가 포함되면 실패시킵니다.
- 코드에서는 순수 도메인만 기대합니다.

### `Check Required Files`

```groovy
test -f "${DEPLOY_DIR}/compose.yaml"
test -f "${DEPLOY_DIR}/common/Jenkinsfile"
test -f "${DEPLOY_DIR}/nginx/conf.d/default.conf"
test -f "${DEPLOY_DIR}/be/Dockerfile"
test -f "${DEPLOY_DIR}/fe/Dockerfile"
test -f "${DEPLOY_DIR}/ai/Dockerfile"
```

- 배포에 반드시 필요한 파일들이 배포 디렉터리에 존재하는지 확인합니다.

### `Check Docker`

```groovy
docker version
docker compose version
```

- 배포 서버에 Docker와 Docker Compose가 사용 가능한지 확인합니다.

### `Validate Compose`

```groovy
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --env-file .env config
```

- Compose 파일과 `.env`를 합쳐 최종 설정을 검증합니다.
- 문법 오류나 환경변수 누락을 조기에 확인하는 단계입니다.

### `Deploy`

```groovy
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --env-file .env build --no-cache frontend nginx fastapi
```

- `frontend`, `nginx`, `fastapi` 이미지를 캐시 없이 새로 빌드합니다.
- 현재 명령은 `spring` 이미지를 명시적으로 빌드하지 않습니다.
- 이후 `up` 단계에서 필요한 경우 빌드될 수 있지만, 캐시 없는 강제 빌드는 세 서비스에만 적용됩니다.

```groovy
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --env-file .env up -d --force-recreate --remove-orphans
```

- 모든 서비스를 백그라운드로 실행합니다.
- 기존 컨테이너를 강제로 재생성합니다.
- 현재 Compose 파일에 없는 오래된 컨테이너는 제거합니다.

### `Check Nginx Config`

```groovy
docker exec project-nginx nginx -t
```

- 실행 중인 Nginx 컨테이너 안에서 Nginx 설정 문법을 검사합니다.

### `Health Check`

```groovy
NETWORK="${PROJECT_NAME}_project-network"
```

- Compose 프로젝트 이름과 네트워크 이름을 조합해 실제 Docker 네트워크 이름을 만듭니다.
- 현재 값은 `marketing_project-network`가 됩니다.

```groovy
docker run --rm --network "$NETWORK" curlimages/curl:latest -fsS http://nginx
```

- 같은 Docker 네트워크에 임시 curl 컨테이너를 띄워 Nginx/프론트엔드 응답을 확인합니다.

```groovy
docker run --rm --network "$NETWORK" curlimages/curl:latest -fsS http://nginx/api/health
```

- Nginx를 통해 Spring health API가 응답하는지 확인합니다.

```groovy
docker run --rm --network "$NETWORK" curlimages/curl:latest -fsS http://nginx/api/ai-health
```

- Spring이 FastAPI와 정상 연결되는지 확인하는 health API를 호출합니다.

각 health check는 최대 30번, 2초 간격으로 재시도합니다. 실패하면 관련 컨테이너 로그를 출력하고 파이프라인을 실패 처리합니다.

### `post`

```groovy
post {
    success {
        echo 'Deploy success.'
    }

    failure {
        echo 'Deploy failed. Check console output.'
    }
}
```

- 파이프라인 성공/실패 시 Jenkins 로그에 결과 메시지를 남깁니다.

## `be/src/main/resources/application.properties`

Spring Boot의 기본 런타임 설정 파일입니다.

```properties
spring.application.name=be
```

- Spring 애플리케이션 이름을 `be`로 설정합니다.

```properties
spring.config.import=optional:file:.env,optional:file:.env.local,optional:file:../.env,optional:file:../.env.local
```

- 실행 위치 기준 현재 디렉터리 또는 상위 디렉터리의 `.env`, `.env.local`을 읽습니다.
- `optional:`이므로 파일이 없어도 애플리케이션 시작 자체는 실패하지 않습니다.

```properties
spring.datasource.url=jdbc:postgresql://${POSTGRES_HOST:localhost}:${POSTGRES_PORT:5432}/${POSTGRES_DB:postgres}
spring.datasource.username=${POSTGRES_USER:postgres}
spring.datasource.password=${POSTGRES_PASSWORD:postgres}
spring.datasource.driver-class-name=org.postgresql.Driver
```

- PostgreSQL 접속 정보를 환경변수에서 읽습니다.
- 환경변수가 없으면 로컬 개발 기본값을 사용합니다.
- Compose에서는 `SPRING_DATASOURCE_URL` 등이 더 높은 우선순위로 주입되어 이 값을 덮어쓸 수 있습니다.

```properties
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
spring.jpa.hibernate.ddl-auto=update
```

- SQL 로그를 출력하고 보기 좋게 포맷합니다.
- `ddl-auto=update`는 엔티티 변경에 맞춰 DB 스키마를 자동 변경합니다.
- 운영 환경에서는 의도치 않은 스키마 변경 위험이 있어 migration 도구 사용을 검토하는 것이 좋습니다.

```properties
spring.data.redis.host=localhost
spring.data.redis.port=6379
spring.data.redis.password=${REDIS_PASSWORD:myredispassword}
```

- Redis 접속 기본값입니다.
- Compose에서는 `SPRING_DATA_REDIS_HOST=redis` 등으로 오버라이드됩니다.

```properties
spring.security.oauth2.client.registration.instagram.*
spring.security.oauth2.client.provider.instagram.*
```

- Instagram OAuth2 로그인/연동 설정입니다.
- client id, secret, redirect uri는 환경변수에서 가져옵니다.
- authorization, token, user-info endpoint를 Instagram API로 지정합니다.

```properties
jwt.secret=${JWT_SECRET}
jwt.access-token-validity-in-ms=3600000
jwt.refresh-token-validity-in-ms=1209600000
```

- JWT 서명 secret과 토큰 만료 시간을 설정합니다.
- Access Token은 1시간, Refresh Token은 14일입니다.

```properties
firebase.service-account-path=classpath:firebase/firebase-service-account.json
```

- Firebase 서비스 계정 JSON을 classpath에서 찾도록 설정합니다.

```properties
springdoc.api-docs.path=/v3/api-docs
springdoc.swagger-ui.path=/swagger-ui.html
```

- Spring Swagger/OpenAPI 문서 경로 설정입니다.

```properties
server.forward-headers-strategy=framework
```

- Nginx 뒤에서 동작할 때 `X-Forwarded-*` 헤더를 Spring이 인식하도록 합니다.
- HTTPS 리다이렉트, Swagger URL 생성, OAuth redirect URL 처리에 영향을 줄 수 있습니다.

## `be/src/main/resources/application-dev.properties`

개발 프로파일용 PostgreSQL 설정입니다.

```properties
spring.datasource.url=jdbc:postgresql://${POSTGRES_HOST:localhost}:${POSTGRES_PORT:5432}/${POSTGRES_DB}
spring.datasource.username=${POSTGRES_USER}
spring.datasource.password=${POSTGRES_PASSWORD}
spring.datasource.driver-class-name=org.postgresql.Driver
```

- `dev` 프로파일에서 사용할 DB 접속 정보입니다.
- 기본 `application.properties`와 달리 DB 이름, 사용자, 비밀번호에 기본값이 없습니다.
- 필요한 환경변수가 없으면 설정 오류가 날 수 있어 개발 환경의 `.env` 준비가 필요합니다.

## `ai/app/core/config.py`

FastAPI 서비스의 런타임 설정을 Pydantic Settings로 관리하는 파일입니다.

```python
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR.parent / ".env"
```

- `ai/app/core/config.py` 기준으로 프로젝트 경로를 계산합니다.
- `.env`는 `ai` 디렉터리의 상위, 즉 저장소 루트의 `.env`를 바라봅니다.

```python
DEFAULT_ORIENTATION_MODEL_WEIGHTS_PATH = ROOT_DIR / "weights" / "model-vit-ang-loss.h5"
DEFAULT_KEYWORD_MODEL_PATH = ROOT_DIR / "models" / "qwen-gguf" / "model.gguf"
```

- AI 모델 파일의 기본 위치를 정의합니다.

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_ignore_empty=True,
        extra="ignore",
    )
```

- 환경변수와 `.env`를 읽어 `Settings` 객체를 만듭니다.
- 빈 환경변수는 무시합니다.
- 정의되지 않은 extra 값은 에러 없이 무시합니다.

```python
PROJECT_NAME: str = "AI Service"
ENVIRONMENT: Literal["local", "staging", "production"] = "local"
HOST: str = "0.0.0.0"
PORT: int = 8000
LOG_LEVEL: str = "DEBUG"
```

- AI 서비스 기본 실행 환경 설정입니다.

```python
PROVIDER: str = "openai"
DEFAULT_MODEL: str = "gpt-4o-mini"
OPENAI_API_KEY: str | None = None
```

- LLM provider와 기본 모델, OpenAI API key 설정입니다.
- API key는 `.env` 또는 컨테이너 환경변수로 주입해야 합니다.

```python
POSTGRES_HOST: str = "postgres"
POSTGRES_PORT: int = 5432
POSTGRES_DB: str
POSTGRES_USER: str
POSTGRES_PASSWORD: str
```

- FastAPI가 PostgreSQL에 접속하기 위한 설정입니다.
- Compose 네트워크 기준 기본 host는 `postgres`입니다.
- DB 이름, 사용자, 비밀번호는 필수값입니다.

```python
REDIS_HOST: str = "redis"
REDIS_PORT: int = 6379
REDIS_PASSWORD: str | None = None
REDIS_DB: int = 0
```

- Redis 접속 설정입니다.
- Compose 기준 기본 host는 `redis`입니다.

```python
S3_SECRET_KEY: str | None = None
S3_ACCESS_KEY: str | None = None
S3_BUCKET_NAME: str | None = None
S3_REGION: str | None = None
CLOUDFRONT_DOMAIN: str | None = None
```

- S3 업로드와 CloudFront URL 생성을 위한 설정입니다.

```python
KEYWORD_MODEL_CTX_SIZE: int = 2048
KEYWORD_MODEL_MAX_TOKENS: int = 64
KEYWORD_MODEL_TEMPERATURE: float = 0.1
KEYWORD_MODEL_TOP_P: float = 0.9
KEYWORD_MODEL_THREADS: int = max((os.cpu_count() or 1) - 2, 1)
KEYWORD_MODEL_GPU_LAYERS: int = 20
KEYWORD_MODEL_ENABLED: bool = True
```

- 키워드 추출 모델의 추론 설정입니다.
- Compose에서는 `KEYWORD_MODEL_GPU_LAYERS`를 `0`으로 덮어써 CPU 실행 쪽으로 조정합니다.

```python
@computed_field
def postgres_dsn(self) -> str:
```

- 개별 DB 설정을 합쳐 `postgresql+asyncpg://...` 형태의 SQLAlchemy async DSN을 만듭니다.

```python
@computed_field
def redis_url(self) -> str:
```

- Redis 접속 URL을 `redis://[:password@]host:port/db` 형태로 만듭니다.

```python
@computed_field
def s3_configured(self) -> bool:
```

- S3 필수 설정이 모두 존재하는지 boolean으로 계산합니다.

```python
settings = Settings()
```

- 애플리케이션 전체에서 import해서 사용할 전역 설정 객체를 생성합니다.

## `fe/vite.config.js`

프론트엔드 빌드 도구인 Vite 설정입니다. 직접적인 서버 인프라는 아니지만, Docker 빌드 결과와 PWA 동작에 영향을 줍니다.

```javascript
plugins: [
  react(),
  tailwindcss(),
  VitePWA({...}),
]
```

- React 플러그인, Tailwind CSS 플러그인, PWA 플러그인을 사용합니다.

```javascript
VitePWA({
  registerType: 'autoUpdate',
  includeAssets: ['favicon.svg'],
```

- PWA service worker를 자동 업데이트 방식으로 등록합니다.
- `favicon.svg`를 PWA asset에 포함합니다.

```javascript
manifest: {
  id: '/',
  name: '맡케팅',
  short_name: '맡케팅',
  description: 'AI 마케팅 도우미',
  lang: 'ko-KR',
  scope: '/',
  theme_color: '#FF7A3D',
  background_color: '#ffffff',
  display: 'standalone',
  start_url: '/',
```

- 브라우저가 이 앱을 설치형 웹앱처럼 인식하기 위한 manifest 정보입니다.
- `display: 'standalone'`은 설치 실행 시 브라우저 UI를 줄이고 앱처럼 보이게 합니다.

```javascript
icons: [
  { src: '/pwa-192x192.png', sizes: '192x192', type: 'image/png' },
  { src: '/pwa-512x512.png', sizes: '512x512', type: 'image/png' },
  {
    src: '/pwa-512x512.png',
    sizes: '512x512',
    type: 'image/png',
    purpose: 'maskable',
  },
]
```

- 모바일 홈 화면이나 설치 앱 아이콘으로 사용할 이미지 목록입니다.
- `maskable`은 Android 등에서 아이콘 모양에 맞춰 잘리지 않도록 여백을 고려한 아이콘 용도입니다.

```javascript
workbox: {
  cleanupOutdatedCaches: true,
  clientsClaim: true,
  skipWaiting: true,
}
```

- 오래된 캐시를 정리합니다.
- 새 service worker가 빠르게 활성화되도록 합니다.
- 이 설정은 배포 후 새 버전 반영 속도에 영향을 줍니다.

```javascript
devOptions: {
  enabled: true,
}
```

- 개발 환경에서도 PWA 기능을 켭니다.
- 개발 중 service worker 캐시 때문에 변경사항이 즉시 안 보일 수 있으니 주의가 필요합니다.

```javascript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}
```

- `@/components/...` 같은 import 경로가 `fe/src`를 가리키도록 별칭을 설정합니다.

## `.gitignore`

Git에 포함하지 않을 파일과 디렉터리를 정의합니다.

### IDE 설정

```gitignore
.idea/
.vscode/
*.iws
*.iml
*.ipr
```

- IntelliJ, VS Code 같은 개인 개발환경 설정을 Git에서 제외합니다.

### 빌드 산출물과 의존성

```gitignore
.gradle/
build/
out/
node_modules/
dist/
__pycache__/
.venv/
```

- Gradle, Node, Python의 빌드 결과와 로컬 의존성 디렉터리를 제외합니다.
- 이런 파일들은 환경마다 다르고 재생성 가능하므로 Git에 올리지 않습니다.

### 운영체제 파일과 로그

```gitignore
.DS_Store
Thumbs.db
*.log
```

- macOS/Windows 자동 생성 파일과 로그 파일을 제외합니다.

### 환경변수와 비밀정보

```gitignore
.env
.env.*
application-local.yml
application-dev.yml
application-prod.yml
```

- DB 비밀번호, API key, secret 등이 들어갈 수 있는 파일을 제외합니다.
- 현재 배포에서는 Jenkins Secret File로 `.env`를 서버에 주입합니다.

### 기타

```gitignore
coverage/
docs-for-me/
nginx/certs/
INFRASTRUCTURE_CODE_GUIDE.md
```

- 테스트 커버리지, 개인 문서, 로컬 인증서, 이 설명 문서를 Git에서 제외합니다.

## 환경변수 흐름

현재 배포 환경변수 흐름은 다음과 같습니다.

```text
Jenkins Credential(marketing-env-file)
  -> common/Jenkinsfile의 Prepare Env 단계
  -> /home/ubuntu/deploy/S14P31A401/.env
  -> docker compose --env-file .env
  -> 각 컨테이너 environment/env_file
  -> Spring application.properties 또는 FastAPI config.py
```

필수로 검증되는 값은 다음과 같습니다.

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `S3_BUCKET_NAME`
- `S3_REGION`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `CLOUDFRONT_DOMAIN`

코드상 추가로 필요할 수 있는 값은 다음과 같습니다.

- `INSTAGRAM_CLIENT_ID`
- `INSTAGRAM_CLIENT_SECRET`
- `OAUTH_REDIRECT_URI`
- `JWT_SECRET`
- `OPENAI_API_KEY`

## 운영 시 주의할 점

- `common/Jenkinsfile`의 캐시 없는 강제 빌드는 현재 `frontend`, `nginx`, `fastapi`만 대상으로 합니다. 백엔드 코드 변경 배포까지 항상 새로 굽고 싶다면 `spring`도 빌드 대상에 포함하는 것이 명확합니다.
- `spring.jpa.hibernate.ddl-auto=update`는 운영 DB 스키마를 자동 변경할 수 있습니다. 운영 안정성이 중요하면 Flyway 또는 Liquibase 같은 migration 도구 사용을 검토하는 것이 좋습니다.
- `depends_on`은 컨테이너 생성 순서만 보장합니다. 실제 readiness는 Jenkins health check에서 보완하고 있습니다.
- PostgreSQL 포트는 `127.0.0.1`에만 열려 있어 외부 노출을 줄이고 있습니다. Redis와 Spring/FastAPI는 외부 포트가 없고 Nginx를 통해서만 접근합니다.
- Nginx 인증서는 호스트의 `/etc/letsencrypt`를 그대로 읽습니다. 인증서 갱신은 호스트 쪽 Certbot 관리 상태에 의존합니다.

## 현재 변경사항 분석

이 섹션은 현재 Git 작업트리에서 `compose.yaml`, 각 `Dockerfile`, `common/Jenkinsfile`에 들어간 변경이 무엇인지, 왜 필요한지 분석한 내용입니다.

### 변경 요약

이번 변경의 핵심은 두 가지입니다.

- Docker 이미지에 실제 배포된 Git 커밋 SHA를 라벨로 남깁니다.
- Jenkins 배포 시 모든 애플리케이션 이미지를 무조건 다시 빌드하지 않고, 변경된 서비스만 선택적으로 빌드하고 재기동합니다.

변경된 파일은 다음입니다.

- `compose.yaml`
- `nginx/Dockerfile`
- `be/Dockerfile`
- `fe/Dockerfile`
- `ai/Dockerfile`
- `common/Jenkinsfile`

### `compose.yaml` 변경

각 build 설정에 `args`가 추가되었습니다.

```yaml
build:
  context: ./nginx
  dockerfile: Dockerfile
  args:
    BUILD_COMMIT: ${BUILD_COMMIT:-unknown}
```

같은 구조가 `nginx`, `spring`, `frontend`, `fastapi` 서비스에 모두 추가되었습니다.

#### 무엇이 바뀌었나

이전에는 Docker Compose가 이미지를 빌드할 때 Git 커밋 정보를 Dockerfile에 전달하지 않았습니다.

이제는 `BUILD_COMMIT`이라는 build argument를 각 Dockerfile에 넘깁니다.

```yaml
BUILD_COMMIT: ${BUILD_COMMIT:-unknown}
```

- `BUILD_COMMIT` 환경변수가 있으면 그 값을 사용합니다.
- 없으면 `unknown`을 사용합니다.

#### 왜 바뀌었나

배포 후 운영 서버에서 “이 컨테이너가 정확히 어떤 Git 커밋으로 만들어졌는지” 확인하기 위해서입니다.

Jenkins에서 다음처럼 값을 export합니다.

```sh
export BUILD_COMMIT="${GIT_COMMIT:-unknown}"
```

그 값이 Compose build args를 통해 Dockerfile로 전달되고, 최종 이미지 라벨에 저장됩니다.

#### 결과

배포 후 다음 명령으로 컨테이너 이미지에 기록된 커밋을 확인할 수 있습니다.

```sh
docker inspect project-spring --format 'spring={{ index .Config.Labels "org.opencontainers.image.revision" }}'
```

장애 분석, 롤백 판단, “서버에 최신 코드가 정말 올라갔는지” 확인할 때 유용합니다.

### `nginx/Dockerfile` 변경

추가된 부분은 다음입니다.

```dockerfile
# 배포 후 docker inspect로 실제 배포된 Git 커밋을 확인하기 위한 이미지 메타데이터
ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.revision=$BUILD_COMMIT
```

그리고 파일 마지막 줄에 newline이 추가되었습니다.

#### 무엇이 바뀌었나

- `ARG BUILD_COMMIT=unknown`이 추가되었습니다.
- `LABEL org.opencontainers.image.revision=$BUILD_COMMIT`이 추가되었습니다.
- 파일 끝 newline이 보정되었습니다.

#### 왜 바뀌었나

Nginx 이미지에도 Git revision metadata를 남기기 위해서입니다.

`org.opencontainers.image.revision`은 OCI 이미지 라벨 관례에서 소스 revision을 나타낼 때 쓰는 표준적인 라벨 이름입니다.

#### 주의할 점

`ARG`는 이미지 빌드 시점에만 사용할 수 있는 값입니다. 컨테이너 실행 중 환경변수와는 다릅니다.

이 값은 `LABEL`로 이미지 메타데이터에 박히기 때문에, 컨테이너 실행 후에도 `docker inspect`로 확인할 수 있습니다.

### `be/Dockerfile` 변경

추가된 부분은 다음입니다.

```dockerfile
# 배포 후 docker inspect로 실제 배포된 Git 커밋을 확인하기 위한 이미지 메타데이터
ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.revision=$BUILD_COMMIT
```

#### 무엇이 바뀌었나

Spring Boot 최종 실행 이미지 단계에 Git revision 라벨이 추가되었습니다.

현재 위치는 두 번째 stage입니다.

```dockerfile
FROM eclipse-temurin:21-jre
WORKDIR /app

ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.revision=$BUILD_COMMIT
```

#### 왜 이 위치에 들어갔나

`be/Dockerfile`은 멀티 스테이지 빌드입니다.

- 첫 번째 stage: JDK로 JAR를 빌드합니다.
- 두 번째 stage: JRE로 실제 실행 이미지를 만듭니다.

운영에서 실행되는 이미지는 두 번째 stage입니다. 따라서 라벨도 최종 stage에 있어야 `docker inspect project-spring`으로 확인할 수 있습니다.

#### 결과

Spring 컨테이너가 어떤 Git 커밋으로 빌드되었는지 확인할 수 있습니다.

### `fe/Dockerfile` 변경

추가된 부분은 다음입니다.

```dockerfile
# 배포 후 docker inspect로 실제 배포된 Git 커밋을 확인하기 위한 이미지 메타데이터
ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.revision=$BUILD_COMMIT
```

#### 무엇이 바뀌었나

프론트엔드 최종 Nginx 이미지에 Git revision 라벨이 추가되었습니다.

현재 위치는 두 번째 stage입니다.

```dockerfile
FROM nginx:1.27-alpine

ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.revision=$BUILD_COMMIT
```

#### 왜 이 위치에 들어갔나

`fe/Dockerfile`도 멀티 스테이지 빌드입니다.

- 첫 번째 stage: Node/pnpm으로 React/Vite 앱을 빌드합니다.
- 두 번째 stage: Nginx로 `dist` 정적 파일을 서빙합니다.

운영에서 실제 실행되는 것은 두 번째 Nginx 이미지이므로, 최종 stage에 라벨을 추가한 것이 맞습니다.

### `ai/Dockerfile` 변경

추가된 부분은 다음입니다.

```dockerfile
# 배포 후 docker inspect로 실제 배포된 Git 커밋을 확인하기 위한 이미지 메타데이터
ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.revision=$BUILD_COMMIT
```

#### 무엇이 바뀌었나

FastAPI 이미지에 Git revision 라벨이 추가되었습니다.

#### 왜 바뀌었나

AI 서비스는 모델, 의존성, Python 코드 변경에 따라 장애 원인이 달라질 수 있습니다. 배포된 컨테이너가 어떤 커밋에서 만들어졌는지 확인할 수 있으면 문제 추적이 쉬워집니다.

### `common/Jenkinsfile` 변경

Jenkinsfile은 이번 변경에서 가장 많이 바뀐 파일입니다.

큰 변화는 다음입니다.

- `Detect Changed Services` stage가 새로 추가되었습니다.
- `Deploy` stage가 무조건 `--no-cache` 빌드 후 전체 재생성하던 방식에서, 변경된 이미지만 빌드하고 해당 컨테이너만 재생성하는 방식으로 바뀌었습니다.
- 배포 후 각 컨테이너의 이미지 revision 라벨을 출력합니다.

### 새 stage: `Detect Changed Services`

새로 추가된 stage입니다.

```groovy
stage('Detect Changed Services') {
    steps {
        sh '''
            set -eu
            ...
        '''
    }
}
```

#### 무엇을 하는가

이 stage는 이전 성공 커밋과 현재 커밋 사이에서 어떤 파일이 바뀌었는지 보고, 어떤 서비스 이미지를 다시 빌드할지 결정합니다.

결과는 `.build-services` 파일에 저장됩니다.

예를 들어 백엔드 파일만 바뀌었다면:

```text
spring
```

프론트엔드와 Nginx가 바뀌었다면:

```text
frontend nginx
```

처럼 저장됩니다.

#### 기준 커밋 계산

```sh
BASE_COMMIT="${GIT_PREVIOUS_SUCCESSFUL_COMMIT:-${GIT_PREVIOUS_COMMIT:-}}"
```

- 우선 `GIT_PREVIOUS_SUCCESSFUL_COMMIT`을 사용합니다.
- 없으면 `GIT_PREVIOUS_COMMIT`을 사용합니다.
- 둘 다 없으면 빈 값입니다.

`GIT_PREVIOUS_SUCCESSFUL_COMMIT`은 마지막으로 성공한 Jenkins 빌드의 커밋입니다. 이 값을 기준으로 잡으면, 중간에 실패한 배포가 있어도 마지막 성공 배포 이후의 변경사항을 다시 포함할 수 있습니다.

#### 이전 커밋이 없거나 유효하지 않을 때

```sh
if [ -z "$BASE_COMMIT" ] || ! git cat-file -e "$BASE_COMMIT^{commit}" 2>/dev/null; then
  echo "No valid previous commit. Build all application images."
  echo "spring frontend nginx fastapi" > "$BUILD_SERVICES_FILE"
  exit 0
fi
```

이전 커밋을 알 수 없으면 전체 애플리케이션 이미지를 빌드합니다.

이 상황은 첫 배포, Jenkins job 초기 실행, Git history가 충분하지 않은 checkout에서 발생할 수 있습니다.

#### 변경 파일 목록 계산

```sh
TARGET_COMMIT="${GIT_COMMIT:-HEAD}"
CHANGED_FILES="$(git diff --name-only "$BASE_COMMIT" "$TARGET_COMMIT")"
```

- 현재 배포 대상 커밋은 `GIT_COMMIT`입니다.
- 없으면 `HEAD`를 사용합니다.
- `git diff --name-only`로 변경된 파일 경로만 가져옵니다.

#### 서비스 선택 로직

```sh
if printf '%s\n' "$CHANGED_FILES" | grep -Eq '^(compose\.yaml|common/Jenkinsfile)$'; then
  SERVICES="spring frontend nginx fastapi"
else
  printf '%s\n' "$CHANGED_FILES" | grep -Eq '^be/' && SERVICES="$(append_service "$SERVICES" spring)"
  printf '%s\n' "$CHANGED_FILES" | grep -Eq '^fe/' && SERVICES="$(append_service "$SERVICES" frontend)"
  printf '%s\n' "$CHANGED_FILES" | grep -Eq '^nginx/' && SERVICES="$(append_service "$SERVICES" nginx)"
  printf '%s\n' "$CHANGED_FILES" | grep -Eq '^ai/' && SERVICES="$(append_service "$SERVICES" fastapi)"
fi
```

매핑은 다음과 같습니다.

- `be/` 변경 -> `spring` 빌드
- `fe/` 변경 -> `frontend` 빌드
- `nginx/` 변경 -> `nginx` 빌드
- `ai/` 변경 -> `fastapi` 빌드
- `compose.yaml` 또는 `common/Jenkinsfile` 변경 -> 전체 애플리케이션 이미지 빌드

#### 왜 `compose.yaml`과 `common/Jenkinsfile` 변경은 전체 빌드인가

두 파일은 특정 서비스 하나의 소스만이 아니라 배포 방식, build args, 서비스 의존성, 네트워크, 환경변수 전달 방식에 영향을 줄 수 있습니다.

따라서 어느 서비스가 영향을 받았는지 좁게 판단하기보다 전체 애플리케이션 이미지를 다시 빌드하는 쪽이 더 안전합니다.

#### `append_service` 함수의 역할

```sh
append_service() {
  services="$1"
  service="$2"

  echo "$services" | grep -Eq "(^| )${service}( |$)" && {
    echo "$services"
    return
  }

  echo "$services $service" | xargs
}
```

서비스 이름이 중복으로 들어가지 않게 추가하는 함수입니다.

예를 들어 이미 `frontend`가 들어 있는데 다시 `frontend`를 추가하려 하면 그대로 반환합니다.

### 변경된 `Deploy` stage

기존 Deploy 단계는 다음 방식이었습니다.

```sh
docker compose ... build --no-cache frontend nginx fastapi
docker compose ... up -d --force-recreate --remove-orphans
```

즉:

- `frontend`, `nginx`, `fastapi`를 항상 캐시 없이 빌드했습니다.
- 그 다음 모든 서비스를 force recreate했습니다.
- `spring`은 `--no-cache` 명시 대상이 아니었습니다.

현재 Deploy 단계는 다음 흐름으로 바뀌었습니다.

1. `.build-services`에서 빌드할 서비스 목록을 읽습니다.
2. `BUILD_COMMIT`을 현재 Jenkins 커밋으로 export합니다.
3. 서버에 이미지가 없으면 해당 서비스를 빌드 목록에 강제로 추가합니다.
4. 빌드 대상이 있으면 해당 서비스만 `docker compose build`합니다.
5. `postgres`, `redis`를 먼저 보장합니다.
6. 변경된 서비스만 `--no-deps --force-recreate`로 재생성합니다.
7. 마지막에 `docker compose up -d --remove-orphans`로 전체 Compose 상태를 정리합니다.
8. 실행 중인 컨테이너와 이미지 revision 라벨을 출력합니다.

#### `.build-services` 읽기

```sh
BUILD_SERVICES="$(cat .build-services 2>/dev/null || true)"
```

앞 stage에서 만든 `.build-services` 파일을 읽습니다.

파일이 없으면 빈 값으로 계속 진행합니다.

현재 `Prepare Deploy Directory` stage가 Jenkins workspace를 `DEPLOY_DIR`로 복사하므로, `.build-services`도 배포 디렉터리에 포함됩니다.

#### `BUILD_COMMIT` export

```sh
export BUILD_COMMIT="${GIT_COMMIT:-unknown}"
```

Compose build args에서 사용할 환경변수입니다.

이 값이 `compose.yaml`의 `${BUILD_COMMIT:-unknown}`으로 들어가고, 다시 Dockerfile의 `ARG BUILD_COMMIT`으로 전달됩니다.

#### 이미지 존재 여부 보정

```sh
docker image inspect marketing-spring:latest >/dev/null 2>&1 || BUILD_SERVICES="$(append_service "$BUILD_SERVICES" spring)"
docker image inspect marketing-frontend:latest >/dev/null 2>&1 || BUILD_SERVICES="$(append_service "$BUILD_SERVICES" frontend)"
docker image inspect marketing-fastapi:latest >/dev/null 2>&1 || BUILD_SERVICES="$(append_service "$BUILD_SERVICES" fastapi)"
docker image inspect "${PROJECT_NAME}-nginx" >/dev/null 2>&1 || BUILD_SERVICES="$(append_service "$BUILD_SERVICES" nginx)"
```

Git diff 기준으로는 변경이 없어도, 서버에 이미지가 아예 없으면 컨테이너를 띄울 수 없습니다.

그래서 이미지가 없는 서비스는 빌드 대상에 강제로 추가합니다.

#### Nginx 이미지 이름이 다른 이유

`spring`, `frontend`, `fastapi`는 `compose.yaml`에 `image:`가 명시되어 있습니다.

```yaml
image: marketing-spring:latest
image: marketing-frontend:latest
image: marketing-fastapi:latest
```

반면 `nginx`는 `image:`가 없습니다.

Compose는 image 이름이 없으면 보통 프로젝트 이름과 서비스 이름을 조합한 이미지를 만듭니다. 현재 Jenkins의 `PROJECT_NAME`이 `marketing`이므로 Nginx 이미지는 `${PROJECT_NAME}-nginx`, 즉 `marketing-nginx`로 검사합니다.

#### 선택 빌드

```sh
if [ -n "$BUILD_SERVICES" ]; then
  docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --env-file .env build $BUILD_SERVICES
```

빌드 대상이 있을 때만 해당 서비스 이미지를 빌드합니다.

기존의 `--no-cache`가 제거되었으므로 Docker layer cache를 활용합니다. 이 변경으로 배포 시간이 줄어들 수 있습니다.

#### DB/Redis 먼저 보장

```sh
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --env-file .env up -d postgres redis
```

애플리케이션 컨테이너를 교체하기 전에 공용 인프라 컨테이너인 DB와 Redis가 떠 있도록 합니다.

#### 변경 서비스만 재생성

```sh
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --env-file .env up -d --no-deps --force-recreate $BUILD_SERVICES
```

- `$BUILD_SERVICES`에 들어 있는 서비스만 재생성합니다.
- `--no-deps` 때문에 의존 서비스까지 같이 재생성하지 않습니다.
- `--force-recreate`는 해당 서비스 컨테이너를 새로 만듭니다.

예를 들어 `frontend`만 변경되면 DB, Redis, Spring, FastAPI는 불필요하게 재시작하지 않습니다.

#### 변경된 이미지가 없을 때

```sh
else
  echo "No application image changes detected. Skip image build."
fi
```

애플리케이션 이미지와 관련 없는 파일만 바뀌었다면 빌드와 서비스 재생성을 생략합니다.

#### 최종 Compose 상태 정리

```sh
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --env-file .env up -d --remove-orphans
```

Compose 파일 기준으로 전체 서비스를 다시 한번 맞춥니다.

- 누락된 컨테이너가 있으면 생성합니다.
- 설정상 제거된 orphan 컨테이너는 정리합니다.
- 이미 정상 실행 중인 서비스는 보통 그대로 유지됩니다.

#### 실행 컨테이너 출력

```sh
docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --env-file .env ps
```

배포 후 컨테이너 상태를 Jenkins 로그에 남깁니다.

#### 배포 revision 출력

```sh
docker inspect project-spring --format 'spring={{ index .Config.Labels "org.opencontainers.image.revision" }}' || true
docker inspect project-frontend --format 'frontend={{ index .Config.Labels "org.opencontainers.image.revision" }}' || true
docker inspect project-nginx --format 'nginx={{ index .Config.Labels "org.opencontainers.image.revision" }}' || true
docker inspect project-fastapi --format 'fastapi={{ index .Config.Labels "org.opencontainers.image.revision" }}' || true
```

각 컨테이너 이미지에 들어 있는 Git revision 라벨을 출력합니다.

`|| true`가 붙어 있어 특정 컨테이너 inspect가 실패해도 Jenkins shell 단계 전체가 바로 실패하지 않습니다.

### 이번 변경의 의도

#### 배포 시간 단축

기존에는 `frontend`, `nginx`, `fastapi`를 항상 `--no-cache`로 다시 빌드했습니다. 특히 AI 서비스는 Python 의존성과 네이티브 빌드가 있어 시간이 오래 걸릴 수 있습니다.

변경 후에는 실제 변경된 서비스만 빌드하고 Docker cache도 활용하므로 배포 시간이 줄어듭니다.

#### 불필요한 서비스 재시작 감소

기존 `up -d --force-recreate --remove-orphans`는 전체 서비스 재생성으로 이어질 수 있었습니다.

변경 후에는 바뀐 서비스만 `--no-deps --force-recreate`로 교체합니다. DB/Redis 같은 상태 저장 서비스나 변경 없는 API 서비스를 불필요하게 건드리지 않습니다.

#### 배포 추적성 강화

이미지에 `org.opencontainers.image.revision` 라벨을 남기므로 운영 중인 컨테이너가 어떤 Git 커밋에서 나온 것인지 확인할 수 있습니다.

이것은 다음 상황에서 유용합니다.

- Jenkins는 성공했는데 서버에 실제 새 코드가 올라갔는지 확인할 때
- 장애가 특정 커밋부터 발생했는지 추적할 때
- 롤백 또는 재배포 판단을 할 때

### 현재 변경에서 확인해야 할 주의점

#### `.build-services` 파일 복사 위치

`Detect Changed Services` stage는 Jenkins workspace에 `.build-services`를 만듭니다.

그 다음 `Prepare Deploy Directory` stage가 workspace 전체를 `DEPLOY_DIR`로 복사하므로 현재 구조에서는 `.build-services`도 같이 복사됩니다.

다만 추후 tar exclude 목록에 숨김 파일 전체 제외 같은 규칙이 추가되면 `.build-services`가 누락될 수 있습니다.

#### Spring 변경 감지 누락은 해결됨

기존 Deploy 단계는 `--no-cache frontend nginx fastapi`만 빌드했습니다. 그래서 백엔드 변경이 있을 때 `spring` 이미지 갱신이 명확하지 않았습니다.

이번 변경에서는 `be/` 변경 시 `spring`을 빌드 목록에 넣기 때문에 이 문제가 개선되었습니다.

#### `common/Jenkinsfile`이나 `compose.yaml` 변경 시 전체 애플리케이션 이미지를 빌드함

이는 안전한 선택입니다. 다만 작은 Jenkins 로그 변경만 있어도 전체 빌드가 발생할 수 있으므로, 배포 시간이 민감하면 추후 더 세밀한 조건 분기가 필요할 수 있습니다.

#### Dockerfile 변경 시 해당 서비스만 빌드됨

각 Dockerfile은 서비스 디렉터리 아래에 있습니다.

- `be/Dockerfile` -> `be/` 변경으로 감지되어 `spring` 빌드
- `fe/Dockerfile` -> `fe/` 변경으로 감지되어 `frontend` 빌드
- `nginx/Dockerfile` -> `nginx/` 변경으로 감지되어 `nginx` 빌드
- `ai/Dockerfile` -> `ai/` 변경으로 감지되어 `fastapi` 빌드

따라서 Dockerfile 변경도 정상적으로 각 서비스 빌드 대상에 포함됩니다.

#### 이미지 라벨은 새로 빌드된 이미지에만 갱신됨

변경이 감지되지 않아 어떤 서비스를 빌드하지 않았다면, 그 서비스의 이미지 revision 라벨은 이전 커밋을 계속 가리킵니다.

이것은 정상입니다. 해당 서비스 이미지는 실제로 새로 만들어지지 않았기 때문입니다.

#### 마지막 `up -d --remove-orphans`의 영향

마지막 전체 `up -d --remove-orphans`는 Compose 상태 정리를 위해 필요합니다.

다만 Compose 설정 자체가 바뀐 경우에는 변경된 설정에 따라 컨테이너가 다시 생성될 수 있습니다. 이 동작은 의도된 배포 정합성 보정에 가깝습니다.

#### line ending 경고

`git diff`에서 다음과 같은 경고가 보였습니다.

```text
LF will be replaced by CRLF the next time Git touches it
```

이는 Windows 작업 환경에서 Git의 line ending 설정 때문에 발생하는 경고입니다.

코드 의미 자체가 바뀐 것은 아니지만, Jenkins는 Linux shell에서 실행되므로 shell script가 들어 있는 `common/Jenkinsfile`은 LF 유지가 더 안전합니다. 저장소의 `.gitattributes`로 Jenkinsfile과 Dockerfile의 line ending을 LF로 고정하는 것도 검토할 수 있습니다.
