FROM python:3.13

LABEL org.opencontainers.image.source https://github.com/mrgionsi/remote-checkin

WORKDIR /usr/src/app
COPY . /

RUN pip install --upgrade pip
RUN pip install -r requirements.txt


ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0 --chdir=/usr/src/app"


CMD [ "gunicorn", "application:app" ]