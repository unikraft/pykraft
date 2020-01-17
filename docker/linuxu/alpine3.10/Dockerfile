FROM alpine:3.10

LABEL MAINTAINER="Alexander Jung <alexander.jung@neclab.eu>"

ARG UK_VER=staging
ENV UK_ROOT=/usr/src/unikraft
ENV UK_LIBS=/usr/src/libs

RUN apk --no-cache add \
      alpine-sdk \
      bash \
      wget \
      git \
      bison \
      flex \
      perl \
      ncurses-dev \
      unzip \
      python3 \
  && git clone --progress -b ${UK_VER} https://github.com/unikraft/unikraft.git ${UK_ROOT} \
  && mkdir -p ${UK_LIBS}

WORKDIR /usr/src/apps/app