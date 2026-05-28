# 인프라 장애 대응 체크리스트

이 문서는 Jenkins 배포 실패나 운영 서버 장애가 발생했을 때 어떤 로그를 보고 어떤 순서로 확인할지 정리한 체크리스트입니다.

## 1. Jenkins에서 먼저 볼 것

Jenkins 로그는 실패한 stage를 기준으로 봅니다.

### Checkout SCM 실패

확인할 것:

- `using credential gitlab-repo-credential`가 보이는지
- `Authentication failed`, `repository not found`, `could not read Username` 메시지가 있는지

대응:

- Jenkins `gitlab-repo-credential` credential 확인
- GitLab token 권한 확인
- Jenkins Job의 SCM credential 설정 확인

### Prepare Env 실패

확인할 것:

- `marketing-env-file` credential이 있는지
- `.env created at ...` 로그가 찍혔는지

대응:

- Jenkins `marketing-env-file`을 Secret file로 등록했는지 확인
- 파일 내용이 비어 있지 않은지 확인

### Prepare Firebase Secret 실패

확인할 것:

- `marketing-firebase-service-account-file` credential이 있는지
- `Firebase service account secret file created.` 로그가 찍혔는지

대응:

- Jenkins에 Firebase JSON을 Secret file로 등록
- credential ID가 `marketing-firebase-service-account-file`인지 확인

### Validate Env 실패

확인할 것:

- `.env keys only`에 필요한 key가 모두 있는지
- `ERROR: missing or empty env`
- `ERROR: duplicated env keys`
- `ERROR: FIREBASE_ENABLED should be true or false`

대응:

- `.env` credential 파일의 key 누락/오타 수정
- `VITE_FIREBASE_MEASUREMENT_ID` 철자 확인
- `FIREBASE_ENABLED=true` 또는 `FIREBASE_ENABLED=false`로 설정

주의:

- Jenkins 로그는 key만 출력하고 value는 출력하지 않습니다.
- `.env` 값을 확인해야 할 때도 Jenkins 로그에 직접 출력하지 않습니다.

### Validate Compose 실패

확인할 것:

- `compose.yaml` 문법 오류
- env interpolation 오류
- volume 경로 오류

대응:

서버에서 배포 디렉터리 기준으로 확인합니다.

```sh
cd /home/ubuntu/deploy/S14P31A401
docker compose -p marketing -f compose.yaml --env-file .env config >/dev/null
```

secret 노출 방지를 위해 `>/dev/null` 없이 실행하지 않습니다.

### Build 실패

확인할 것:

- 어떤 이미지에서 실패했는지
- `spring`, `frontend`, `fastapi`, `nginx` 중 어느 서비스인지
- `COPY failed`, `RUN ... returned a non-zero code`, dependency download 실패 여부

자주 보는 패턴:

- `COPY failed: file not found`: Dockerfile이 복사하려는 파일이 build context에 없음
- `pnpm install` 실패: FE lockfile/package 문제
- `./gradlew bootJar` 실패: BE 컴파일/테스트/환경 설정 문제
- `uv sync` 실패: AI dependency/lockfile 문제
- `apt-get` 실패: 네트워크 또는 Debian repository 문제

### Health Check 실패

확인할 것:

- `nginx/frontend health check failed`
- `spring health check failed`
- `ai-health check failed`

대응:

Jenkins 로그에서 실패한 서비스의 `docker compose logs ... --tail=100` 출력부터 확인합니다.

## 2. 서버 접속 후 기본 상태 확인

배포 서버에서 먼저 현재 컨테이너 상태를 봅니다.

```sh
cd /home/ubuntu/deploy/S14P31A401
docker compose -p marketing -f compose.yaml --env-file .env ps
```

확인할 것:

- `nginx`, `frontend`, `spring`, `fastapi`, `postgres`, `redis`가 떠 있는지
- `Restarting`, `Exited`, `Created` 상태가 있는지
- 포트 매핑이 정상인지

전체 컨테이너 상태도 확인할 수 있습니다.

```sh
docker ps -a
```

## 3. 서비스별 로그 확인

최근 로그:

```sh
docker compose -p marketing -f compose.yaml --env-file .env logs nginx --tail=100
docker compose -p marketing -f compose.yaml --env-file .env logs frontend --tail=100
docker compose -p marketing -f compose.yaml --env-file .env logs spring --tail=100
docker compose -p marketing -f compose.yaml --env-file .env logs fastapi --tail=100
docker compose -p marketing -f compose.yaml --env-file .env logs postgres --tail=100
docker compose -p marketing -f compose.yaml --env-file .env logs redis --tail=100
```

실시간 로그:

```sh
docker compose -p marketing -f compose.yaml --env-file .env logs -f spring
```

주의:

- `docker inspect project-spring`처럼 전체 inspect를 찍으면 환경변수가 노출될 수 있습니다.
- 필요한 값만 `--format`으로 출력합니다.

## 4. Nginx 확인

Nginx 설정 문법:

```sh
docker exec project-nginx nginx -t
```

Nginx 로그:

```sh
docker compose -p marketing -f compose.yaml --env-file .env logs nginx --tail=100
```

확인할 것:

- `host not found in upstream`: upstream 서비스 이름 문제 또는 컨테이너 미기동
- `connect() failed`: 대상 서비스가 죽었거나 포트가 다름
- `certificate` 관련 오류: `/etc/letsencrypt` 마운트 또는 인증서 경로 문제

인증서 경로 확인:

```sh
docker exec project-nginx ls -al /etc/letsencrypt/live
```

## 5. Spring 확인

Health check:

```sh
docker run --rm --network marketing_project-network curlimages/curl:latest -fsS http://spring:8080/api/health
```

Nginx 경유:

```sh
docker run --rm --network marketing_project-network curlimages/curl:latest -fsS http://nginx/api/health
```

로그:

```sh
docker compose -p marketing -f compose.yaml --env-file .env logs spring --tail=200
```

자주 보는 패턴:

- DB 연결 실패: `Connection refused`, `password authentication failed`
- Redis 연결 실패: `Unable to connect to Redis`
- JWT 설정 실패: `JWT_SECRET` 누락
- OAuth 설정 실패: Instagram env 누락/redirect URI 불일치
- Firebase 초기화 실패: service account path 또는 JSON 문제

Firebase secret 파일 존재 확인:

```sh
docker exec project-spring ls -al /run/secrets/firebase-service-account.json
```

파일 내용은 출력하지 않습니다.

## 6. FastAPI 확인

Health check:

```sh
docker run --rm --network marketing_project-network curlimages/curl:latest -fsS http://fastapi:8000/ai/health
```

Nginx 경유:

```sh
docker run --rm --network marketing_project-network curlimages/curl:latest -fsS http://nginx/api/ai-health
```

로그:

```sh
docker compose -p marketing -f compose.yaml --env-file .env logs fastapi --tail=200
```

자주 보는 패턴:

- 모델 다운로드 실패
- S3 권한 오류
- Python dependency 오류
- startup이 오래 걸려 health check 타임아웃

## 7. Postgres 확인

상태:

```sh
docker compose -p marketing -f compose.yaml --env-file .env ps postgres
```

로그:

```sh
docker compose -p marketing -f compose.yaml --env-file .env logs postgres --tail=100
```

컨테이너 내부 접속:

```sh
docker exec -it project-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

주의:

- 위 명령은 현재 shell에 env가 있을 때만 동작합니다.
- Jenkins 로그에 DB password를 출력하지 않습니다.

자주 보는 패턴:

- `password authentication failed`: `.env`의 DB 계정/비밀번호와 볼륨에 초기화된 계정이 다름
- `database does not exist`: DB 이름 불일치
- `No space left on device`: 디스크 부족

## 8. Redis 확인

상태:

```sh
docker compose -p marketing -f compose.yaml --env-file .env ps redis
```

로그:

```sh
docker compose -p marketing -f compose.yaml --env-file .env logs redis --tail=100
```

PING 확인:

```sh
docker exec project-redis redis-cli -a '<REDIS_PASSWORD>' ping
```

주의:

- 실제 password를 Jenkins 로그나 공유 채팅에 남기지 않습니다.

## 9. 이미지 Revision 확인

배포된 컨테이너가 어떤 Git commit으로 빌드됐는지 확인합니다.

```sh
docker inspect project-spring --format 'spring={{ index .Config.Labels "org.opencontainers.image.revision" }}'
docker inspect project-frontend --format 'frontend={{ index .Config.Labels "org.opencontainers.image.revision" }}'
docker inspect project-nginx --format 'nginx={{ index .Config.Labels "org.opencontainers.image.revision" }}'
docker inspect project-fastapi --format 'fastapi={{ index .Config.Labels "org.opencontainers.image.revision" }}'
```

확인할 것:

- Jenkins의 `Build commit`과 컨테이너 revision이 같은지
- 특정 서비스만 예전 commit이면 해당 이미지가 재빌드/재생성되지 않은 것

## 10. 변경 서비스 빌드 확인

Jenkins의 `Detect Changed Services` 단계에서 다음 로그를 확인합니다.

```text
Changed files:
Services selected for image build:
```

예상 매핑:

```text
be/**      -> spring
fe/**      -> frontend
ai/**      -> fastapi
nginx/**   -> nginx
compose.yaml 또는 common/Jenkinsfile -> 전체 빌드
```

FE env만 바꾼 경우는 Git diff가 없으므로 frontend가 자동으로 다시 빌드되지 않을 수 있습니다. Vite 환경변수는 빌드 타임에 들어가기 때문에 frontend 이미지를 강제로 다시 빌드해야 반영됩니다.

## 11. 안전하게 재시작하기

특정 서비스만 재시작:

```sh
docker compose -p marketing -f compose.yaml --env-file .env restart spring
```

특정 서비스만 재생성:

```sh
docker compose -p marketing -f compose.yaml --env-file .env up -d --no-deps --force-recreate spring
```

전체 상태 정리:

```sh
docker compose -p marketing -f compose.yaml --env-file .env up -d --remove-orphans
```

주의:

- DB/Redis 볼륨 삭제는 운영 데이터 손실로 이어질 수 있습니다.
- `docker compose down -v`는 운영에서 함부로 사용하지 않습니다.

## 12. 빠른 판단 순서

문제가 생기면 아래 순서로 봅니다.

1. Jenkins에서 실패 stage 확인
2. `docker compose ps`로 컨테이너 상태 확인
3. 실패 서비스 로그 `--tail=100` 확인
4. Nginx 경유 health check와 서비스 직접 health check 비교
5. DB/Redis 의존성 확인
6. 이미지 revision 확인
7. env/secret 누락 여부 확인
8. 필요 시 변경 서비스만 재빌드/재생성
