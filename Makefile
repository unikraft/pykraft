# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Europe Ltd., NEC Corporation. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

KRAFTDIR            ?= $(CURDIR)
DOCKERDIR           ?= $(KRAFTDIR)/docker

ifeq ($(HASH),)
HASH_COMMIT         ?= HEAD # Setting this is only really useful with the show-tag target
HASH                ?= $(shell git update-index -q --refresh && git describe --tags)

ifneq ($(HASH_COMMIT),HEAD) # Others can't be dirty by definition
DIRTY               := $(shell git update-index -q --refresh && git diff-index --quiet HEAD -- $(KRAFTDIR) || echo "-dirty")
endif
endif

REPO                ?= https://github.com/unikraft/kraft
ORG                 ?= unikraft
TAG                 ?= -$(HASH)$(DIRTY)

_EMPTY              :=
_SPACE              := $(_EMPTY) $(_EMPTY)

# Tools
DOCKER              ?= docker
DOCKER_BUILD_EXTRA  ?=
PYTHON              ?= python3

UK_ARCH             ?= x86_64
GCC_VERSION         ?= 9.2.0

.PHONY: docker-kraft
docker-kraft: IMAGE=$(ORG)/kraft:latest
docker-kraft:
	$(DOCKER) build \
		--tag $(IMAGE)$(TAG) \
		--build-arg UK_ARCH=$(UK_ARCH) \
		--build-arg GCC_VERSION=$(GCC_VERSION) \
		--cache-from $(IMAGE) \
		--file $(DOCKERDIR)/Dockerfile.kraft \
		$(DOCKER_BUILD_EXTRA) \
		$(KRAFTDIR)

.PHONY: install
install:
	$(PYTHON) setup.py install

include $(KRAFTDIR)/docker/Makefile
