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
DISTDIR             ?= $(KRAFTDIR)/dist

ifeq ($(HASH),)
HASH_COMMIT         ?= HEAD # Setting this is only really useful with the show-tag target
HASH                ?= $(shell git update-index -q --refresh && git describe --tags)

ifneq ($(HASH_COMMIT),HEAD) # Others can't be dirty by definition
DIRTY               := $(shell git update-index -q --refresh && git diff-index --quiet HEAD -- $(KRAFTDIR) || echo "-dirty")
endif
endif
	
APP_NAME            ?= kraft
PKG_NAME            ?= unikraft-tools
PKG_ARCH            ?= amd64
PKG_VENDOR          ?= debian
PKG_DISTRIBUTION    ?= sid
VERSION             ?= $(shell echo "$(HASH)$(DIRTY)" | tail -c +2)
REPO                ?= https://github.com/unikraft/kraft
ORG                 ?= unikraft
TAG                 ?= -$(HASH)$(DIRTY)

_EMPTY              :=
_SPACE              := $(_EMPTY) $(_EMPTY)

# Tools
FORCE_DOCKER        ?= n
DOCKER              ?= docker
DOCKER_RUN_EXTRA    ?=
DOCKER_RUN          ?= $(DOCKER) run --rm \
                         $(1) $(DOCKER_RUN_EXTRA) \
                         -v $(KRAFTDIR):/usr/src/kraft \
                         unikraft/$(2)
DOCKER_BUILD_EXTRA  ?=
PYTHON              ?= python3
DCH                 ?= dch
DCH_FLAGS           ?=
MK_BUILD_DEPS       ?= mk-build-deps
DEBUILD             ?= debuild
DEBUILD_FLAGS       ?= --preserve-env -b -us -uc
DEB_BUILD_OPTIONS   ?= 'nocheck parallel=6'
RM                  ?= rm
GIT                 ?= git
MKDIR               ?= mkdir
SED                 ?= sed
TAR                 ?= tar
CP                  ?= cp
CD                  ?= cd
RELEASE_NOTES       ?=
READ                ?= read
NIGHTLY             ?= n
SETUPPY_FLAGS       ?= -d $(DISTDIR)
ifeq ($(NIGHTLY),y)
NIGHTLY             := nightly
else
NIGHTLY             := 
endif 

# If run with DOCKER= or within a container, unset DOCKER_RUN so all commands
# are not proxied via docker container.
ifeq ($(FORCE_DOCKER),y)
else ifeq ($(DOCKER),)
DOCKER_RUN          :=
else ifneq ($(wildcard /.dockerenv),)
DOCKER_RUN          :=
endif

.PRE :=
ifneq ($(DOCKER_RUN),)
VARS := $(foreach E, $(shell printenv), -e "$(E)")
.PRE := docker-proxy-
sdist pkg-deb changelog:
	$(info Building all targets via Docker environment!)
	$(call DOCKER_RUN,$(VARS),pkg-deb:$(PKG_VENDOR)-$(PKG_DISTRIBUTION)) $(MAKE) -e $@;
	@exit 0
endif

.PHONY: $(.PRE)pkg-deb
$(.PRE)pkg-deb: $(.PRE)sdist
	$(MKDIR) -p $(DISTDIR)/build
	$(TAR) -x -C $(DISTDIR)/build --strip-components=1 --exclude '*.egg-info' -f $(DISTDIR)/$(PKG_NAME)-$(VERSION).tar.gz
	$(CP) -Rfv $(KRAFTDIR)/package/debian $(DISTDIR)/build
	$(SED) -i -re "1s/..unstable/~$(shell lsb_release -cs)) $(shell lsb_release -cs)/" $(DISTDIR)/build/debian/changelog
	($(CD) $(DISTDIR)/build; $(DEBUILD) $(DEBUILD_FLAGS))

.PHONY: $(.PRE)sdist
$(.PRE)sdist: bump
	$(PYTHON) setup.py $(NIGHTLY) sdist $(SETUPPY_FLAGS)

.PHONY: bump
bump:
	$(SED) -i --regexp-extended "s/__version__[ ='0-9a-zA-Z\.\-]+/__version__ = '$(VERSION)'/g" $(KRAFTDIR)/kraft/__init__.py

.PHONY: bump-commit
bump-commit: COMMIT_MESSAGE ?= "$(APP_NAME) v$(VERSION) released"
bump-commit:
	$(GIT) add $(KRAFTDIR)/kraft/__init__.py $(KRAFTDIR)/Makefile $(KRAFTDIR)/package/debian/changelog
	$(GIT) commit -s -m $(COMMIT_MESSAGE)
	$(GIT) tag -a v$(VERSION) -m $(COMMIT_MESSAGE)

.PHONY: $(.PRE)changelog
$(.PRE)changelog: COMMIT_MESSAGE ?= "$(APP_NAME) v$(VERSION) released"
$(.PRE)changelog: PREV_VERSION ?= $(shell git tag | sort -r | head -1 | awk '{split($$0, tags, "\n")} END {print tags[1]}')
ifeq ($(wildcard $(KRAFTDIR)/package/debian/changelog),)
$(.PRE)changelog: DCH_FLAGS += --create
endif
$(.PRE)changelog:
ifeq ($(findstring $(VERSION),$(shell head -1 $(KRAFTDIR)/package/debian/changelog)),)
	$(CD) $(KRAFTDIR)/package && $(DCH) $(DCH_FLAGS) -M \
		-v "$(VERSION)" \
		--package $(PKG_NAME) \
		--distribution $(PKG_DISTRIBUTION) \
		"$(APP_NAME) v$(VERSION) released"
	$(GIT) log --format='%s' $(PREV_VERSION)..HEAD | sort -r | while read line; do \
		echo "Found change: $$line"; \
		(cd $(KRAFTDIR)/package && $(DCH) -M -a "$$line"); \
	done;
endif

.PHONY: get-version
get-version:
	@echo $(VERSION)

.PHONY: install
install:
	$(PYTHON) setup.py install

.PHONY: clean
clean:
	@$(RM) -Rfv $(DISTDIR)/build/*

.PHONY: properclean
properclean:
	@$(RM) -Rfv $(DISTDIR)/*

include $(KRAFTDIR)/package/docker/Makefile
