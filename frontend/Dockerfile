FROM nginx:alpine

LABEL org.opencontainers.image.source=https://github.com/mrgionsi/remote-checkin

COPY nginx.conf /etc/nginx/conf.d/default.conf


COPY dist/remote-checkin/browser /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]