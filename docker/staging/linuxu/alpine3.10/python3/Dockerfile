FROM unikraft/staging:linuxu-alpine3.10-pthread-embedded-amd64 AS pthread
FROM unikraft/staging:linuxu-alpine3.10-openssl-amd64          AS openssl
FROM unikraft/staging:linuxu-alpine3.10-libuuid-amd64          AS libuuid
FROM unikraft/staging:linuxu-alpine3.10-newlib-amd64           AS newlib
FROM unikraft/staging:linuxu-alpine3.10-lwip-amd64             AS lwip
FROM unikraft/staging:linuxu-alpine3.10-zlib-amd64             AS zlib
FROM unikraft/staging:linuxu-alpine3.10-amd64                  AS unikraft

LABEL MAINTAINER="Alexander Jung <alexander.jung@neclab.eu>"

COPY --from=pthread /usr/src/libs/pthread-embedded /usr/src/libs/pthread-embedded
COPY --from=openssl /usr/src/libs/openssl          /usr/src/libs/openssl
COPY --from=libuuid /usr/src/libs/libuuid          /usr/src/libs/libuuid
COPY --from=newlib  /usr/src/libs/newlib           /usr/src/libs/newlib
COPY --from=lwip    /usr/src/libs/lwip             /usr/src/libs/lwip
COPY --from=zlib    /usr/src/libs/zlib             /usr/src/libs/zlib

ARG UK_VER=staging
RUN apk --no-cache add \
      perl \
      python3 \
 && git clone --progress -b ${UK_VER} https://github.com/unikraft/lib-python3.git ${UK_LIBS}/python3