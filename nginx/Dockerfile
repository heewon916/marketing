FROM nginx:1.27-alpine

# 기본 설정 파일 삭제 및 커스텀 설정 파일 복사
RUN rm -f /etc/nginx/conf.d/default.conf
COPY conf.d /etc/nginx/conf.d
COPY certs /etc/nginx/certs

# html 디렉터리가 존재하고 별도의 정적 파일 서빙이 필요하다면 아래 주석 해제
# COPY html /usr/share/nginx/html