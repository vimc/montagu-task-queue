FROM python:3.6


WORKDIR /home/worker
COPY requirements.txt ./
RUN pip install --no-cache-dir -r ./requirements.txt && \
        rm ./requirements.txt

ENV PATH="/home/root/.local/bin:${PATH}"

COPY src ./src

COPY config/docker_config.yml ./config/config.yml
COPY config/email_templates ./config/email_templates

ENTRYPOINT ["celery", "-A", "src", "worker", "-l", "INFO"]