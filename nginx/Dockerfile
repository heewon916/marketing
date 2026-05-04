FROM nginx:1.27-alpine

# 배포 후 docker inspect로 실제 배포된 Git 커밋을 확인하기 위한 이미지 메타데이터
ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.revision=$BUILD_COMMIT

# 기본 설정 파일 삭제 및 커스텀 설정 파일 복사
RUN rm -f /etc/nginx/conf.d/default.conf
COPY conf.d /etc/nginx/conf.d

# html 디렉터리가 존재하고 별도의 정적 파일 서빙이 필요하다면 아래 주석 해제
# COPY html /usr/share/nginx/html
