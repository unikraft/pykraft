FROM unikraft/lib-pthread:staging-linuxu-alpine3.10-embedded-amd64 AS pthread
FROM unikraft/lib-openssl:staging-linuxu-alpine3.10-amd64          AS openssl
FROM unikraft/lib-libuuid:staging-linuxu-alpine3.10-amd64          AS libuuid
FROM unikraft/lib-newlib:staging-linuxu-alpine3.10-amd64           AS newlib
FROM unikraft/lib-lwip:staging-linuxu-alpine3.10-amd64             AS lwip
FROM unikraft/lib-zlib:staging-linuxu-alpine3.10-amd64             AS zlib
FROM unikraft/unikraft:staging-linuxu-alpine3.10-amd64             AS unikraft

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