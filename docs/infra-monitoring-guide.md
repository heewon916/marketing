# 운영 모니터링 가이드

작성일: 2026-05-12

## 목적

운영 중 컨테이너가 내려가거나 메모리 부족으로 죽는 상황을 확인하기 위해 Prometheus, Alertmanager, Grafana, cAdvisor, node-exporter를 사용한다.

- `node-exporter`: EC2 호스트 CPU, 메모리, 디스크, 네트워크 지표
- `cAdvisor`: Docker 컨테이너별 CPU, 메모리, 재시작 추적에 필요한 컨테이너 지표
- `Prometheus`: 지표 수집, alert rule 평가, 저장
- `Alertmanager`: Prometheus alert를 Mattermost webhook으로 전달
- `Grafana`: 지표 대시보드
- `blackbox-exporter`: Nginx와 API endpoint를 사용자 관점에서 HTTP probe

## 구성

모니터링은 앱 배포용 `compose.yaml`과 분리된 `monitoring/compose.monitoring.yaml`로 실행한다.

다음 컨테이너가 생성된다.

```text
project-prometheus
project-alertmanager
project-grafana
project-blackbox-exporter
project-cadvisor
project-node-exporter
```

외부 노출을 줄이기 위해 Prometheus, Alertmanager, Grafana는 EC2 localhost에만 포트를 바인딩한다.

```text
127.0.0.1:9090 -> Prometheus
127.0.0.1:9093 -> Alertmanager
127.0.0.1:3000 -> Grafana
```

운영 서버 밖에서 접속하려면 SSH 터널을 사용한다.

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 -L 9093:127.0.0.1:9093 ubuntu@서버주소
```

브라우저에서 다음 주소로 접속한다.

```text
http://127.0.0.1:3000
```

## 배포

배포 서버에서 실행한다.

```bash
cd /home/ubuntu/deploy/S14P31A401
sudo docker compose -p marketing-monitoring -f monitoring/compose.monitoring.yaml --env-file .env up -d
```

모니터링 compose는 앱 compose와 별도 프로젝트로 실행한다. 일반 Jenkins 배포의 `docker compose up -d --remove-orphans`가 앱 compose에서 실행되어도 모니터링 컨테이너를 orphan으로 정리하지 않는다.

Jenkins 배포 이후 앱 compose를 다시 올려도 이미 실행 중인 모니터링 컨테이너는 유지된다.

```bash
sudo docker compose -p marketing-monitoring -f monitoring/compose.monitoring.yaml --env-file .env ps
```

## Grafana 로그인

기본값은 다음과 같다.

```text
ID: admin
Password: change-me
```

운영에서는 Jenkins Credential의 `.env`에 아래 값을 지정한다.

```env
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=강한_비밀번호
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
PROMETHEUS_RETENTION_TIME=15d
ALERTMANAGER_PORT=9093
MATTERMOST_WEBHOOK_URL=https://mattermost.example.com/hooks/...
MATTERMOST_USERNAME=Prometheus
```

`MATTERMOST_WEBHOOK_URL`은 Jenkins Credential의 `.env`에만 저장하고 Git에 커밋하지 않는다. Mattermost 채널은 incoming webhook을 만들 때 지정한 기본 채널을 사용한다.

## 알림 규칙

기본 alert rule은 `monitoring/prometheus/rules/infra-alerts.yml`에 있다.

- `HostHighMemoryUsage`: 호스트 메모리 사용률 90% 초과가 5분 지속
- `HostCriticalMemoryUsage`: 호스트 메모리 사용률 95% 초과가 2분 지속
- `HostDiskUsageHigh`: root 디스크 사용률 85% 초과가 10분 지속
- `ContainerHighMemoryUsage`: `project-*` 컨테이너 메모리 working set이 1GiB 초과로 5분 지속
- `SpringContainerDown`: `project-spring` 지표가 1분 이상 cAdvisor에서 사라짐
- `FastApiContainerDown`: `project-fastapi` 지표가 1분 이상 cAdvisor에서 사라짐
- `NginxContainerDown`: `project-nginx` 지표가 1분 이상 cAdvisor에서 사라짐
- `PostgresContainerDown`: `project-postgres` 지표가 1분 이상 cAdvisor에서 사라짐
- `RedisContainerDown`: `project-redis` 지표가 1분 이상 cAdvisor에서 사라짐
- `HttpEndpointDown`: Nginx 또는 주요 API endpoint가 2분 이상 HTTP 200을 반환하지 않음. 502 Bad Gateway, 5xx, timeout, 연결 실패를 잡는다.
- `HttpEndpointSlow`: 주요 HTTP endpoint 응답 시간이 5분 이상 3초를 초과함

Alertmanager는 Mattermost incoming webhook을 Slack 호환 webhook으로 사용한다.

현재 HTTP probe 대상은 `monitoring/prometheus/prometheus.yml`의 `blackbox-http` job에 있다.

```text
http://project-nginx
http://project-nginx/api/health
http://project-nginx/api/ai-health
```

모니터링 compose는 앱 compose의 Docker network에 붙어서 내부 Nginx를 직접 확인한다. 앱 compose 프로젝트 이름을 바꾼 경우 `.env`에 실제 네트워크 이름을 지정한다.

```env
APP_DOCKER_NETWORK=marketing_project-network
```

## 먼저 볼 지표

컨테이너 메모리 사용량:

```promql
container_memory_working_set_bytes{name!=""}
```

컨테이너별 메모리 사용량 상위 10개:

```promql
topk(10, container_memory_working_set_bytes{name!=""})
```

호스트 메모리 사용률:

```promql
100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))
```

컨테이너 CPU 사용률:

```promql
rate(container_cpu_usage_seconds_total{name!=""}[5m])
```

호스트 디스크 사용률:

```promql
100 * (1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"})
```

## 장애 시 확인 순서

컨테이너 상태:

```bash
sudo docker compose -p marketing -f /home/ubuntu/deploy/S14P31A401/compose.yaml --env-file /home/ubuntu/deploy/S14P31A401/.env ps
```

모니터링 컨테이너 상태:

```bash
cd /home/ubuntu/deploy/S14P31A401
sudo docker compose -p marketing-monitoring -f monitoring/compose.monitoring.yaml --env-file .env ps
```

최근 OOM kill 여부:

```bash
sudo dmesg -T | grep -i 'killed process\|out of memory\|oom'
```

컨테이너별 현재 리소스:

```bash
sudo docker stats --no-stream
```

Spring 최근 로그:

```bash
sudo docker compose -p marketing -f /home/ubuntu/deploy/S14P31A401/compose.yaml --env-file /home/ubuntu/deploy/S14P31A401/.env logs spring --tail=200
```

FastAPI 최근 로그:

```bash
sudo docker compose -p marketing -f /home/ubuntu/deploy/S14P31A401/compose.yaml --env-file /home/ubuntu/deploy/S14P31A401/.env logs fastapi --tail=200
```

## 주의사항

Grafana, Prometheus, Alertmanager 포트는 `127.0.0.1`에만 바인딩한다. `0.0.0.0`으로 열면 인증과 방화벽 설정 전에는 외부에 운영 지표가 노출될 수 있다.

cAdvisor는 Docker 컨테이너 지표 수집을 위해 호스트 경로를 read-only로 마운트한다. 운영 서버에서만 실행하고, 불필요하게 외부 포트를 열지 않는다.
