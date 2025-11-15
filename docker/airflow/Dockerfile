FROM apache/airflow:latest
LABEL org.opencontainers.image.authors="mail@bsantanna.me"
ENV REFRESHED_AT=2025-11-15

USER root

RUN apt update -qq && \
    apt install -yqq --no-install-recommends git && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN cd /tmp/ && \
    git clone https://github.com/bsantanna/quant-agents.git && \
    cd /tmp/quant-agents && chown airflow:root /tmp/quant-agents/ && \
    cp -a /tmp/quant-agents/dags ${AIRFLOW_HOME}/dags/

USER airflow
