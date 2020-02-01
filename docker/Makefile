# Makefile for Unikraft's Docker-based build system
#
# Copyright (C) 2020 by Alexander Jung <a.jung@lancs.ac.uk>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
WORKDIR             ?= $(CURDIR)
UK_VER              ?= staging
UK_PLAT             ?= linuxu # Default to userspace apps
UK_PLAT_VER_LATEST  ?= $(shell cat $(CURDIR)/$(1))
UK_PLAT_VER         ?= $(call PLAT_VER_LATEST,$(PLAT))
UK_PLATS            ?= linuxu \
                       xen4.11
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
HASH                ?= $(shell git ls-tree --full-tree $(HASH_COMMIT) -- $(CURDIR) | awk '{print $$3}')

ifneq ($(HASH_COMMIT),HEAD) # Others can't be dirty by definition
DIRTY               := $(shell git update-index -q --refresh && git diff-index --quiet HEAD -- $(CURDIR) || echo "-dirty")
endif
endif

REPO                ?= https://github.com/unikraft/tools
ORG                 ?= unikraft
TAG                 ?= -$(HASH)$(DIRTY)

_EMPTY              :=
_SPACE              := $(_EMPTY) $(_EMPTY)

DOCKER              ?= docker
EXTRA_DOCKER        ?=

# QEMU build targets
QEMU_VERSION        ?= 4.2.0

.PHONY: qemu
qemu: IMAGE=$(ORG)/tools:qemu$(QEMU_VERSION)$(TAG)
qemu:
	$(DOCKER) build \
		--build-arg QEMU_VERSION=$(QEMU_VERSION) \
		--tag $(IMAGE) \
		--cache-from $(IMAGE) \
		--file $(WORKDIR)/Dockerfile.qemu \
		$(EXTRA_DOCKER) \
		.

# GCC build targets
GCC_VERSION         ?= 9.2.0
BINUTILS_VERSION    ?= 2.31.1
GLIB_VERSION        ?= 2.11

.PHONY: gcc
gcc: IMAGE=$(ORG)/tools:gcc$(GCC_VERSION)-$(UK_ARCH)$(TAG)
gcc:
	$(DOCKER) build \
		--build-arg UK_ARCH=$(UK_ARCH) \
		--build-arg GCC_VERSION=$(GCC_VERSION) \
		--build-arg BINUTILS_VERSION=$(BINUTILS_VERSION) \
		--build-arg GLIB_VERSION=$(GLIB_VERSION) \
		--tag $(IMAGE) \
		--cache-from $(IMAGE) \
		--file $(WORKDIR)/Dockerfile.gcc \
		$(EXTRA_DOCKER) \
		.

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
		--cache-from $(ORG)/tools:linuxk$1-$3$(TAG) \
		--file $(WORKDIR)/Dockerfile.linuxk \
		$(EXTRA_DOCKER) \
		.

$2-$3: linuxk$1-$3
	$(DOCKER) build \
		--build-arg UK_VER=$(UK_VER) \
		--build-arg UK_KERN=$1 \
		--build-arg UK_PLAT=$2 \
		--build-arg UK_LIB=$(UK_LIB) \
		--build-arg UK_ARCH=$3 \
		--tag $(ORG)/$(if $(UK_LIB),lib-$(UK_LIB):$(LIB_VER),unikraft:$(UK_VER))-$(subst $(_SPACE),$(_DASH),$(strip $2 $3)) \
		--cache-from $(ORG)/$(if $(UK_LIB),lib-$(UK_LIB):$(LIB_VER),unikraft:$(UK_VER))-$(subst $(_SPACE),$(_DASH),$(strip $2 $3)) \
		--file $(WORKDIR)/$2/Dockerfile \
		$(EXTRA_DOCKER) \
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
	$(eval $(call include-plat,$(P))) \
)
