# Program arguments
UK_VER          ?= staging
PLAT            ?= linuxu
PLATS           ?= kvm              \
                   linuxu           \
                   solo5            \
                   xen
DIST            ?= alpine
DIST_VER_LATEST ?= $(shell cat $(CURDIR)/$(PLAT)/$(1))
DIST_VER        ?= $(call DIST_VER_LATEST,$(DIST))
DISTS           ?= alpine           \
                   centos           \
                   ubuntu
LIB             ?= 
LIBS            ?= libuuid          \
                   lwip             \
                   newlib           \
                   openssl          \
                   pthread-embedded \
                   zlib             \
                   click            \
                   python3
ARCH            ?= amd64
ARCHS           ?= amd64
TAG             ?=

_DASH           := -
_EMPTY          :=
_SPACE          := $(_EMPTY) $(_EMPTY)
IMAGE           ?= unikraft

# Tools
DOCKER          ?= docker
DOCKER_BUILD    ?= $(DOCKER) build \
	--build-arg UK_VER=$(UK_VER) \
	--build-arg UK_PLAT=$(1) \
	--build-arg UK_DIST=$(2) \
	--build-arg UK_LIB=$(3) \
	--build-arg UK_ARCH=$(4) \
	-f $(CURDIR)/$(1)/$(2)/$(3)/Dockerfile \
	-t $(IMAGE)/$(UK_VER):$(subst $(_SPACE),$(_DASH),$(strip $(1) $(2) $(3) $(4))) \
	$(CURDIR)/$(1)/$(2)/$(3)

# Format: unikraft/$(UK_VER):$(PLAT)-$(DIST_VER)-$(LIB)-$(ARCH)

.PHONY: all
all:
	$(call DOCKER_BUILD,$(PLAT),$(DIST_VER),$(LIB),$(ARCH))

# Build all the libraries with the set plat/dist/arch
.PHONY: libs $(LIBS)
libs: $(LIBS)
$(LIBS):
	$(call DOCKER_BUILD,$(PLAT),$(DIST_VER),$@,$(ARCH))

.PHONY: distros
distros: alpine

# Populate targets with known distributions and their versions
define distro
.PHONY: $(1)
$(1): $(call DIST_VER_LATEST,$(1))

.PHONY: $(1)$(2)
$(1)$(2): DIST=$(1)
$(1)$(2):
	$(call DOCKER_BUILD,$(PLAT),$(1)$(2),,$(ARCH))
endef

$(eval $(call distro,alpine,3.10))

# .PHONY: platforms
# platforms: xen
# xen: PLAT=xen
# xen: 
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST_VER),,$(ARCH))

# .PHONY: archs
# archs: x86_64
# x86_64:
