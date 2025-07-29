FROM python3.13-slim

RUN apt update
RUN apt -y upgrade

COPY ./requirements.txt .
RUN pip install -r requirements.txt

# run gunicorn workers as unprivileged user
RUN adduser --home /app app

COPY . /app
WORKDIR /app
USER app

# still running directly for debugging
ENTRYPOINT ["/usr/local/bin/python3", "/app/main.py", "--config-file", "/app/config.yml"]
