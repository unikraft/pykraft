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

DOCKERDIR             := $(dir $(lastword $(MAKEFILE_LIST)))

UK_VER              ?= staging
UK_PLAT             ?= linuxu # Default to userspace apps
UK_PLAT_VER_LATEST  ?= $(shell cat $(DOCKERDIR)/$(1))
UK_PLAT_VER         ?= $(call PLAT_VER_LATEST,$(PLAT))
UK_PLATS            ?= linuxu
UK_LIB              ?= # Specify a specific library build
UK_LIB_VER          ?= staging
UK_LIBS             ?= libuuid \
                       lwip \
                       newlib \
                       openssl \
                       pthread-embedded \
                       zlib \
                       click \
                       python3
UK_ARCH             ?= x86_64
UK_ARCHS            ?= x86_64 \
                       arm \
                       arm64

ifeq ($(HASH),)
HASH_COMMIT         ?= HEAD # Setting this is only really useful with the show-tag target
HASH                ?= $(shell git update-index -q --refresh && git describe --tags)

ifneq ($(HASH_COMMIT),HEAD) # Others can't be dirty by definition
DIRTY               := $(shell git update-index -q --refresh && git diff-index --quiet HEAD -- $(DOCKERDIR) || echo "-dirty")
endif
endif

REPO                ?= https://github.com/unikraft/kraft
ORG                 ?= unikraft
TAG                 ?= -$(HASH)$(DIRTY)

_EMPTY              :=
_SPACE              := $(_EMPTY) $(_EMPTY)

DOCKER              ?= docker
DOCKER_BUILD_EXTRA  ?=

# QEMU build targets
QEMU_VERSION        ?= 4.2.0

.PHONY: docker-qemu
docker-qemu: IMAGE=$(ORG)/qemu:$(QEMU_VERSION)
docker-qemu:
	$(DOCKER) build \
		--build-arg QEMU_VERSION=$(QEMU_VERSION) \
		--tag $(IMAGE)$(TAG) \
		--cache-from $(IMAGE) \
		--file $(DOCKERDIR)/Dockerfile.qemu \
		$(DOCKER_BUILD_EXTRA) \
		$(DOCKERDIR)

# GCC build targets
GCC_VERSION         ?= 9.2.0
BINUTILS_VERSION    ?= 2.31.1
GLIB_VERSION        ?= 2.11

.PHONY: docker-gcc
docker-gcc: IMAGE=$(ORG)/gcc:$(GCC_VERSION)-$(UK_ARCH)
docker-gcc:
	$(DOCKER) build \
		--build-arg UK_ARCH=$(UK_ARCH) \
		--build-arg GCC_VERSION=$(GCC_VERSION) \
		--build-arg BINUTILS_VERSION=$(BINUTILS_VERSION) \
		--build-arg GLIB_VERSION=$(GLIB_VERSION) \
		--tag $(IMAGE) \
		--cache-from $(IMAGE)$(TAG) \
		--file $(DOCKERDIR)/Dockerfile.gcc \
		$(DOCKER_BUILD_EXTRA) \
		$(DOCKERDIR)

# kern-plat-arch populates a target image based on kernel, platform, and
# architecture in the format:
#
# 	unikraft/tools:linuxk$(LINUXK_VERSION)-$(UK_ARCH)
#   unikraft/unikraft:$(PLAT)-$(UK_ARCH)
#
# such that the following example commands:
#
# 	make linuxk4.4.4-xen4.12-x86_64
# 	make linuxk5.4.4-kvm-x86_64
#   make xen4.12-x86_64
#   make xen-arm64
#   ..etc..
#
# can be used to directly create a desired environment.
define kern-plat-arch
TARGETS += linuxk$1-$3 $2-$3

.PHONY: linuxk$1-$3 $2-$3
all: linuxk$1-$2-$3

linuxk$1-$2-$3: linuxk$1-$3
$2: linuxk$1-$2-$3

linuxk$1-$3:
	$(DOCKER) build \
		--build-arg LINUXK_VERSION=$1 \
		--build-arg UK_ARCH=$3 \
		--tag $(ORG)/tools:linuxk$1-$3$(TAG) \
		--cache-from $(ORG)/tools:linuxk$1-$3 \
		--file $(DOCKERDIR)/Dockerfile.linuxk \
		$(DOCKER_BUILD_EXTRA) \
		$(DOCKERDIR)

$2-$3: linuxk$1-$3
	$(DOCKER) build \
		--build-arg UK_VER=$(UK_VER) \
		--build-arg UK_KERN=$1 \
		--build-arg UK_PLAT=$2 \
		--build-arg UK_LIB=$(UK_LIB) \
		--build-arg UK_ARCH=$3 \
		--tag $(ORG)/$(if $(UK_LIB),lib-$(UK_LIB):$(LIB_VER),unikraft:$(UK_VER))-$(subst $(_SPACE),$(_DASH),$(strip $2 $3)) \
		--cache-from $(ORG)/$(if $(UK_LIB),lib-$(UK_LIB):$(LIB_VER),unikraft:$(UK_VER))-$(subst $(_SPACE),$(_DASH),$(strip $2 $3)) \
		--file $(DOCKERDIR)/$2/Dockerfile \
		$(DOCKER_BUILD_EXTRA) \
		$2
endef

.PHONY: list
list:
	@echo "Available make targets:\n"
	@for target in $(TARGETS); do \
		echo " *" $$target ; \
	done

.DEFAULT_GOAL       := all
.PHONY: all
all: $(TARGETS)

.PHONY: plats
plats: $(UK_PLATS)

# Iterate through all platforms (and thier versions, in the case for Xen
# project) and include their local Makefile.in file.  This will trigger the
# creation of relevant kernel targets for this platform.
define include-plat
$(eval include $1/Makefile.in)
$(foreach K_V,$(KERNEL_VERSIONS), \
	$(foreach K_A,$(wildcard $1/linuxk-$(shell echo $(K_V) | cut -d . -f 1-2)*), \
		$(eval $(call kern-plat-arch,$(K_V),$1,$(shell echo $(K_A) | cut -d - -f 3))) \
	) \
)
endef

$(foreach P,$(UK_PLATS), \
	$(eval $(call include-plat,$(DOCKERDIR)/$(P))) \
)
