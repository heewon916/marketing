# Firebase Secret 배포 경로 트러블슈팅 기록

작성일: 2026-05-12

## 요약

운영 서버에서 Firebase service account JSON이 파일이 아니라 디렉터리로 마운트되는 문제가 있었다.

최종 원인은 Jenkins 컨테이너가 파일을 생성하는 경로와 Docker Compose가 bind mount로 읽는 EC2 호스트 경로가 서로 다른 파일시스템을 보고 있었기 때문이다.

## 배포 구조

Jenkinsfile의 배포 경로는 다음과 같다.

```groovy
environment {
    DEPLOY_DIR = '/home/ubuntu/deploy/S14P31A401'
    COMPOSE_FILE = 'compose.yaml'
    PROJECT_NAME = 'marketing'
}
```

Firebase secret은 Jenkins Credential의 Secret file에서 받아 다음 경로로 복사한다.

```bash
/home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
```

`compose.yaml`의 Spring 서비스는 이 파일을 컨테이너 내부로 bind mount한다.

```yaml
volumes:
  - type: bind
    source: ./secrets/firebase-service-account.json
    target: /run/secrets/firebase-service-account.json
    read_only: true
    bind:
      create_host_path: false
```

## 증상

EC2 호스트에서 secret 경로를 확인했을 때 파일이 아니라 디렉터리였다.

```bash
ls -ld /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
```

문제 상태:

```text
drwxr-xr-x ... /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
```

Spring 컨테이너 내부에서도 같은 경로가 디렉터리로 보였다.

```bash
docker exec project-spring sh -c 'ls -ld /run/secrets/firebase-service-account.json'
```

문제 상태:

```text
drwxr-xr-x ... /run/secrets/firebase-service-account.json
```

이 상태에서는 Spring이 Firebase service account JSON을 파일로 읽을 수 없다.

## 원인 분석

Jenkins는 Docker 컨테이너로 실행 중이었다.

```bash
docker ps | grep -i jenkins
```

Jenkins 컨테이너 내부에서는 Firebase secret이 정상적인 파일로 생성되어 있었다.

```bash
docker exec -it jenkins sh -c 'ls -ld /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json'
```

확인 결과:

```text
-rw------- 1 root root ... /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
```

하지만 EC2 호스트의 같은 경로는 디렉터리였다.

즉 실제 상태는 다음과 같았다.

```text
Jenkins 컨테이너 내부:
/home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
=> 파일

EC2 호스트:
/home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
=> 디렉터리

Spring 컨테이너:
/run/secrets/firebase-service-account.json
=> EC2 호스트 경로를 bind mount하므로 디렉터리
```

Docker Compose의 bind mount는 Jenkins 컨테이너 내부 파일이 아니라 Docker daemon이 실행되는 EC2 호스트 파일시스템을 기준으로 동작한다.

## 조치 내용

Jenkins 자체를 실행하는 `/opt/jenkins/compose.yaml`에 EC2 호스트의 deploy 디렉터리를 Jenkins 컨테이너에도 같은 경로로 마운트했다.

```yaml
services:
  jenkins:
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - /usr/bin/docker:/usr/bin/docker
      - /home/ubuntu/marketing:/home/ubuntu/marketing
      - /home/ubuntu/deploy:/home/ubuntu/deploy
      - /usr/libexec/docker/cli-plugins/docker-compose:/usr/local/lib/docker/cli-plugins/docker-compose:ro
```

Jenkins 컨테이너를 재생성했다.

```bash
cd /opt/jenkins
docker compose up -d
```

EC2 호스트에 잘못 생성되어 있던 디렉터리를 삭제했다.

```bash
sudo rm -rf /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
```

이후 Jenkins 수동 빌드를 다시 실행하여 secret file을 다시 생성했다.

EC2 호스트에서 파일로 생성된 것을 확인했다.

```bash
ls -ld /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
test -f /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json && echo file
```

정상 상태:

```text
-rw------- ... /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
file
```

## Spring 컨테이너 재생성

기존 Spring 컨테이너는 디렉터리였던 시점의 bind mount 상태를 들고 있을 수 있으므로 컨테이너를 재생성했다.

```bash
sudo docker compose -p marketing \
  -f /home/ubuntu/deploy/S14P31A401/compose.yaml \
  --env-file /home/ubuntu/deploy/S14P31A401/.env \
  up -d --force-recreate spring
```

이 명령은 이미지를 다시 빌드하지 않는다. 기존 Spring 이미지를 그대로 사용하고 Spring 컨테이너만 재생성하여 현재 compose 설정, `.env`, volume mount를 다시 반영한다.

컨테이너 내부에서 secret이 파일로 보이는지 확인했다.

```bash
sudo docker exec project-spring sh -c 'ls -ld /run/secrets/firebase-service-account.json; test -f /run/secrets/firebase-service-account.json && echo file; test -d /run/secrets/firebase-service-account.json && echo dir'
```

정상 상태:

```text
-rw------- ... /run/secrets/firebase-service-account.json
file
```

## 확인 명령 모음

Jenkins 컨테이너가 실행 중인지 확인:

```bash
docker ps | grep -i jenkins
```

Jenkins 컨테이너의 mount 확인:

```bash
docker inspect jenkins --format '{{ range .Mounts }}{{ .Source }} -> {{ .Destination }}{{ println }}{{ end }}'
```

Spring 컨테이너가 어떤 compose working directory에서 생성되었는지 확인:

```bash
docker inspect project-spring --format '{{ index .Config.Labels "com.docker.compose.project.working_dir" }}'
```

Spring 컨테이너의 mount 확인:

```bash
docker inspect project-spring --format '{{ range .Mounts }}{{ .Type }} {{ .Source }} -> {{ .Destination }}{{ println }}{{ end }}'
```

EC2 호스트의 Firebase secret 파일 확인:

```bash
ls -ld /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json
test -f /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json && echo file
test -d /home/ubuntu/deploy/S14P31A401/secrets/firebase-service-account.json && echo dir
```

Spring 컨테이너 내부의 Firebase secret 파일 확인:

```bash
sudo docker exec project-spring sh -c 'ls -ld /run/secrets/firebase-service-account.json; test -f /run/secrets/firebase-service-account.json && echo file; test -d /run/secrets/firebase-service-account.json && echo dir'
```

## 주의사항

Jenkins가 컨테이너로 실행되는 경우 Jenkinsfile에 적힌 절대경로가 EC2 호스트 경로와 같아 보이더라도 실제로는 Jenkins 컨테이너 내부 파일시스템일 수 있다.

Docker Compose bind mount는 Docker daemon이 실행되는 호스트 파일시스템을 기준으로 동작한다. 따라서 Jenkins가 생성하는 파일과 Docker가 mount하는 파일이 같은 실제 파일이 되려면 Jenkins 컨테이너에 호스트 deploy 디렉터리를 volume으로 마운트해야 한다.

`.env`는 Jenkins Credential의 `marketing-env-file`에서 배포 시 `/home/ubuntu/deploy/S14P31A401/.env`로 복사된다. 운영 서버에서 직접 내용을 확인할 때는 민감값이 로그나 채팅에 노출되지 않도록 필요한 key만 grep한다.

```bash
sudo grep -n '^FIREBASE_ENABLED\|^FIREBASE_SERVICE_ACCOUNT_PATH' /home/ubuntu/deploy/S14P31A401/.env
```

운영에서 bind mount한 Firebase secret을 사용하려면 Spring이 바라보는 경로도 컨테이너 내부 파일 경로와 일치해야 한다.

```env
FIREBASE_SERVICE_ACCOUNT_PATH=file:/run/secrets/firebase-service-account.json
```

`classpath:firebase/firebase-service-account.json`는 jar 내부 리소스를 찾는 설정이므로, `/run/secrets/firebase-service-account.json`로 마운트한 운영 secret 파일을 사용하지 않는다.
