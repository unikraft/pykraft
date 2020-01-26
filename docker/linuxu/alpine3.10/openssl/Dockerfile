FROM unikraft/unikraft:staging-linuxu-alpine3.10-amd64 AS unikraft

LABEL MAINTAINER="Alexander Jung <alexander.jung@neclab.eu>"

ARG UK_VER=staging

RUN git clone --progress https://github.com/unikraft/lib-openssl.git ${UK_LIBS}/openssl