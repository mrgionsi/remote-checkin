FROM python:3.13

LABEL org.opencontainers.image.source=https://github.com/mrgionsi/remote-checkin

WORKDIR /usr/src/app
COPY . .
RUN apk add --no-cache mesa-gl

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0 --chdir=/usr/src/app"

EXPOSE 8000
CMD [ "gunicorn", "wsgi:app" ]