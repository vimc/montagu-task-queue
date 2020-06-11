FROM python:3

WORKDIR /
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
        rm requirements.txt

COPY src /src

COPY config/docker_config.yml /config/config.yml

ENTRYPOINT ["celery", "-A", "src", "worker", "-l", "info"]