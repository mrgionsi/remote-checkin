FROM python:3.11

LABEL org.opencontainers.image.source https://github.com/mrgionsi/remote-checkin

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]
