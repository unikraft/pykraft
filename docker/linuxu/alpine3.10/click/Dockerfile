FROM unikraft/lib-newlib:staging-linuxu-alpine3.10-amd64 AS newlib
FROM unikraft/lib-lwip:staging-linuxu-alpine3.10-amd64   AS lwip
FROM unikraft/unikraft:staging-linuxu-alpine3.10-amd64   AS unikraft

LABEL MAINTAINER="Alexander Jung <alexander.jung@neclab.eu>"

COPY --from=newlib  /usr/src/libs/newlib           /usr/src/libs/newlib
COPY --from=lwip    /usr/src/libs/lwip             /usr/src/libs/lwip

ARG UK_VER=staging

RUN git clone --progress -b ${UK_VER} https://github.com/unikraft/lib-click.git ${UK_LIBS}/click