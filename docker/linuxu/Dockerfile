ARG GCC_VERSION=9.2.0
ARG UK_ARCH=x86_64

FROM unikraft/tools:gcc${GCC_VERSION}-${UK_ARCH} AS gcc
FROM ubuntu:19.10

LABEL MAINTAINER="Alexander Jung <a.jung@lancs.ac.uk>"

WORKDIR ${UK_APP}

ARG UK_VER=staging
ENV UK_APPS=/usr/src/apps \
    UK_APP=${UK_APPS}/app \
    UK_ROOT=/usr/src/unikraft \
    UK_LIBS=/usr/src/libs \
    UK_UID=1001 \
    UK_GID=1001 \
    TERM=xterm-256color \
    PWD=${UK_APP}

RUN groupadd -g ${UK_GID} unikraft; \
    useradd -g ${UK_UID} -u ${UK_UID} -M unikraft; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      build-essential \
      libncurses-dev \
      flex \
      wget \
      bison \
      unzip \
      python3

COPY --from=gcc /bin/* /bin/

USER ${UK_UID}
