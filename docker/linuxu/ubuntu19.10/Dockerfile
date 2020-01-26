FROM ubuntu:19.10

LABEL MAINTAINER="Alexander Jung <alexander.jung@neclab.eu>"

ARG UK_VER=staging
ENV UK_APPS=/usr/src/apps
ENV UK_APP=${UK_APPS}/app
ENV UK_ROOT=/usr/src/unikraft
ENV UK_LIBS=/usr/src/libs
ENV UK_UID=1001
ENV UK_GID=1001

WORKDIR ${UK_APP}
ENV PWD=${UK_APP}

RUN groupadd -g ${UK_GID} unikraft \
 && useradd -g ${UK_UID} -u ${UK_UID} -M unikraft \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libncurses-dev \
      flex \
      bison \
      python3 

USER ${UK_UID}
