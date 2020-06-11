FROM python:3.6

RUN adduser --disabled-login  worker
USER worker

WORKDIR /home/worker
COPY --chown=worker:worker requirements.txt ./
RUN pip install --user --no-cache-dir -r ./requirements.txt && \
        rm ./requirements.txt

ENV PATH="/home/worker/.local/bin:${PATH}"

COPY --chown=worker:worker src ./src

COPY --chown=worker:worker config/docker_config.yml ./config/config.yml

ENTRYPOINT ["celery", "-A", "src", "worker", "-l", "info"]