FROM docker.io/python:3.6-slim-buster

ARG REPO=git+git://github.com/grnet/bmcmanager.git
ARG BRANCH=master

RUN apt-get update && \
    apt-get -y install --no-install-recommends \
        git \
        ipmitool \
        freeipmi && \
    rm -rf /var/lib/apt/lists && \
    pip install --no-cache-dir ${REPO}@${BRANCH} && \
    apt-get purge git -y && \
    apt-get autoremove -y
