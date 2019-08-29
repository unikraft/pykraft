FROM golang:1.12.7-alpine3.10 AS local

ARG SRC_DIR=/go/src/github.com/unikraft/tools
WORKDIR ${SRC_DIR}
COPY . ${SRC_DIR}

RUN apk --no-cache add \
      make \
      git

FROM local AS build

ARG SRC_DIR=/go/src/github.com/unikraft/tools

RUN cd ${SRC_DIR} \
 && make build

FROM alpine:3.10 AS binary

ARG SRC_DIR=/go/src/github.com/unikraft/tools
COPY --from=build ${SRC_DIR}/tools /tools

ENTRYPOINT [ "/tools" ]