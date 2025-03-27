FROM python:3.13

LABEL org.opencontainers.image.source=https://github.com/mrgionsi/remote-checkin

WORKDIR /usr/src/app
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi:app"]
