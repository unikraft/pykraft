FROM alpine:3.10

LABEL MAINTAINER="Alexander Jung <alexander.jung@neclab.eu>"

ARG UK_VER=staging
ENV UK_APPS=/usr/src/apps
ENV UK_APP=${UK_APPS}/app
ENV UK_ROOT=/usr/src/unikraft
ENV UK_LIBS=/usr/src/libs
ENV UK_UID=1001
ENV UK_GID=1001

WORKDIR ${UK_APP}

RUN adduser -u ${UK_UID} -g ${UK_GID} -D unikraft \  
 && apk --no-cache add \
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
  && mkdir -p ${UK_LIBS} \
  && mkdir -p ${UK_APPS} \
  && chown -Rf ${UK_UID}:${UK_GID} ${UK_ROOT} ${UK_LIBS} ${UK_APPS}

USER ${UK_UID}

