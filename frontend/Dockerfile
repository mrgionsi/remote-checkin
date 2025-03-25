FROM nginx:alpine

LABEL org.opencontainers.image.source https://github.com/mrgionsi/remote-checkin

COPY dist/ /usr/share/nginx/html

CMD ["nginx", "-g", "daemon off;"]
