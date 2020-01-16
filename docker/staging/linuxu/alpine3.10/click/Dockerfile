FROM unikraft/staging:linuxu-alpine3.10-newlib           AS newlib
FROM unikraft/staging:linuxu-alpine3.10-lwip             AS lwip
FROM unikraft/staging:linuxu-alpine3.10                  AS unikraft

LABEL MAINTAINER="Alexander Jung <alexander.jung@neclab.eu>"

COPY --from=newlib  /usr/src/libs/newlib           /usr/src/libs/newlib
COPY --from=lwip    /usr/src/libs/lwip             /usr/src/libs/lwip

ARG UK_VER=staging

RUN git clone --progress -b ${UK_VER} https://github.com/unikraft/lib-click.git ${UK_LIBS}/click