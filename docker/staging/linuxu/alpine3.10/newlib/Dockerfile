FROM unikraft/staging:linuxu-alpine3.10-amd64 AS unikraft

LABEL MAINTAINER="Alexander Jung <alexander.jung@neclab.eu>"

ARG UK_VER=staging

RUN git clone --progress -b ${UK_VER} https://github.com/unikraft/lib-newlib.git ${UK_LIBS}/newlib