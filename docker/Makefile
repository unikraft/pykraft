# Program arguments
UK_VER ?= staging
DIST   ?= alpine3.10
DISTS  ?= alpine           \
          centos           \
		  ubuntu
PLAT   ?= linuxu
PLATS  ?= kvm              \
          linuxu           \
	      solo5            \
          xen
LIB    ?= 
LIBS   ?= libuuid          \
          lwip             \
          newlib           \
          openssl          \
          pthread-embedded \
          zlib             \
		  click            \
          python3
ARCH   ?= amd64
ARCHS  ?= amd64
TAG    ?=

_DASH  := -
_EMPTY :=
_SPACE := $(_EMPTY) $(_EMPTY)
IMAGE  ?= unikraft

# Tools
DOCKER ?= docker
DOCKER_BUILD ?= $(DOCKER) build \
	--build-arg UK_VER=$(UK_VER) \
	--build-arg UK_PLAT=$(1) \
	--build-arg UK_DIST=$(2) \
	--build-arg UK_LIB=$(3) \
	--build-arg UK_ARCH=$(4) \
	-f $(CURDIR)/$(UK_VER)/$(1)/$(2)/$(3)/Dockerfile \
	-t $(IMAGE)/$(UK_VER):$(subst $(_SPACE),$(_DASH),$(strip $(1) $(2) $(3) $(4))) \
	$(CURDIR)/$(UK_VER)/$(1)/$(2)/$(3)

# Format: unikraft/$(VER):$(PLAT)-$(DIST)-$(LIB)-$(ARCH)

.PHONY: all
all:
	$(call DOCKER_BUILD,$(PLAT),$(DIST),$(LIB),$(ARCH))

.PHONY: libs $(LIBS)
libs: $(LIBS)
$(LIBS):
	$(call DOCKER_BUILD,$(PLAT),$(DIST),$@,$(ARCH))

.PHONY: distros
distros: alpine ubuntu

.PHONY: alpine alpine3.10 alpine3.9 alpine3.8
# alpine: alpine3.10 alpine3.9 alpine3.8
alpine: DIST=alpine
alpine:
	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))
alpine3.10: DIST=alpine3.10
alpine3.10:
	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))
# alpine3.9: DIST=alpine3.9
# alpine3.9:
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))
# alpine3.8: DIST=alpine3.8
# alpine3.8:
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))

# .PHONY: ubuntu ubuntu19.10 ubuntu18.10 ubuntu18.04
# ubuntu: ubuntu19.10 ubuntu19.04 ubuntu18.10
# ubuntu19.10: DIST=ubuntu.19.10
# ubuntu19.10:
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))
# ubuntu19.04: DIST=ubuntu.19.04
# ubuntu19.04:
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))
# ubuntu18.10: DIST=ubuntu.18.10
# ubuntu18.10:
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))

# .PHONY: cento centos8 centos7 centos6
# centos: centos8 centos7 centos6
# centos8: DIST=centos8
# centos8:
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))
# centos7: DIST=centos7
# centos7:
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))
# centos6: DIST=centos6
# centos6:
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))

# .PHONY: platforms
# platforms: xen
# xen: PLAT=xen
# xen: 
# 	$(call DOCKER_BUILD,$(PLAT),$(DIST),,$(ARCH))

# .PHONY: archs
# archs: x86_64
# x86_64:
