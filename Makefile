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

KRAFTDIR             ?= $(CURDIR)
DOCKERDIR            ?= $(KRAFTDIR)/docker
DISTDIR              ?= $(KRAFTDIR)/dist

ifeq ($(HASH),)
HASH_COMMIT          ?= HEAD
HASH                 ?= $(shell git update-index -q --refresh && \
                                git describe --tags)

# Others can't be dirty by definition
ifneq ($(HASH_COMMIT),HEAD)
HASH_COMMIT          ?= HEAD
endif
DIRTY                ?= $(shell git update-index -q --refresh && \
                                git diff-index --quiet HEAD -- $(KRAFTDIR) || \
                                echo "-dirty")
endif

APP_NAME             ?= kraft
PKG_NAME             ?= unikraft-tools
PKG_ARCH             ?= amd64
PKG_VENDOR           ?= debian
PKG_DISTRIBUTION     ?= sid
APP_VERSION          ?= $(shell echo "$(HASH)$(DIRTY)" | tail -c +2)
REPO                 ?= https://github.com/unikraft/kraft
ORG                  ?= unikraft


# Make uilities
_EMPTY               :=
_SPACE               := $(_EMPTY) $(_EMPTY)
Q                    ?= @


# Docker
FORCE_DOCKER         ?= n
FORCE_DOCKER_BUILD   ?= n
DOCKER               ?= docker
DOCKER_RUN_EXTRA     ?=
DOCKER_RUN           ?= $(DOCKER) run --rm \
                          $(1) $(DOCKER_RUN_EXTRA) \
                          -v $(KRAFTDIR):/usr/src/kraft \
                          unikraft/$(2)
DOCKER_BUILD_EXTRA   ?=

# Tools
SNAKE                ?= python3
RM                   ?= rm
GIT                  ?= git
MKDIR                ?= mkdir
SED                  ?= sed
TAR                  ?= tar
CP                   ?= cp
CD                   ?= cd


# Setup Make's default goal
.DEFAULT_GOAL        := all
.PHONY: all
all: help


.PHONY: help
help:
ifeq ($(subst help,,$(MAKECMDGOALS)),)
	@echo "Usage: [FLAGS=...] $(MAKE) TARGET                                             "
	@echo "                                                                              "
	@echo "  kraft's build system is designed to help package, test and release the      "
	@echo "  unikraft-tools software suite.  To find out more information about a specfic"
	@echo "  target listed below, use:                                                   "
	@echo "                                                                              "
	@echo "    make help TARGET                                                          "
	@echo "                                                                              "
	@echo "  If you are trying to install kraft, please refer to our getting started     "
	@echo "  guide: https://unikraft.org/getting-started.  If you are a developer wishing"
	@echo "  to make changes to kraft, please refer to the CONTRIBUTING.md document      "
	@echo "  located in this repository.                                                 "
	@echo "                                                                              "
	@echo "General targets:                                                              "
	@echo "  install                  Install kraft and other unikraft tools.            "
	@echo "  clean                    Clean build artifacts excluding packages.          "
	@echo "  properclean              Clean everything.                                  "
	@echo "  get-version              Show the current version of the application.       "
	@echo "  help                     Show this help menu.                               "
	@echo "                                                                              "
	@echo "Developer targets:                                                            "
	@echo "  release-commit           Commit and tag a release to the repository.        "
	@echo "  changelog                Produce a changelog based on the git log.          "
	@echo "  bump                     Increment kraft's release version in the source    "
	@echo "                             repository.                                      "
	@echo "                                                                              "
	@echo "Docker container build targets:                                               "
	@echo "  docker-gcc               Build gcc and binutils in Docker container.        "
	@echo "  docker-qemu              Build qemu in a Docker container.                  "
	@echo "  docker-kraft             Build the kraft Docker container.                  "
	@echo "  docker-linuxk            Build the Linux kernel in a container.             "
	@echo "  docker-pkg-deb           Build a Debian-based packaging environment.        "
	@echo "  docker-pkg-deb-all       Build all Deban-based packaging environments.      "
	@echo "                                                                              "
	@echo "Packaging targets:                                                            "
	@echo "  sdist                    Produce a distributable tarball of the source tree."
	@echo "  pkg-deb                  Produce a Debian-based package.                    "
	@echo "                                                                              "
	@echo "Test targets:                                                                 "
	@echo "  test                     Run all test targets.                              "
	@echo "  test-all                 Alias for 'make test'.                             "
	@echo "  test-lint                Perform a syntax check on kraft.                   "
	@echo "  test-pkg                 Test the installation of kraft packages.           "
	@echo "  test-unit                Run all defined unit tests.                        "
	@echo "  test-coverage            Generate a coverage report.                        "
	@echo "  test-docker-pkg-deb      Test the installation of a Debian-based package.   "
	@echo "  test-docker-pkg-deb-all  Test the installation of all Debian-based packages."
	@echo "                                                                              "
	@echo "Docker proxy:                                                                 "
	@echo "  Some targets are automatically proxied via a Docker container so as to      "
	@echo "  ensure consistency between runtime environments.  To turn off proxying      "
	@echo "  targets via Docker, ensure that requirements-dev.txt has been satisfied then"
	@echo "  simply unset the DOCKER variable, for example:                              "
	@echo "                                                                              "
	@echo "    DOCKER= make test                                                         "
	@echo "                                                                              "
	@echo "Help:                                                                         "
	@echo "  For help using this tool, please open an issue on the Github repository:    "
	@echo "  $(REPO) or send an email to our maling list:                                "
	@echo "  <unikraft@listserv.neclab.eu>.                                              "
	@echo
else
	@echo -n
endif


# If run with DOCKER= or within a container, unset DOCKER_RUN so all commands
# are not proxied via docker container.
ifeq ($(FORCE_DOCKER),y)
else ifeq ($(DOCKER),)
DOCKER_RUN           :=
else ifneq ($(wildcard /.dockerenv),)
DOCKER_RUN           :=
else ifneq (,$(findstring help,$(MAKECMDGOALS)))
DOCKER_RUN           :=
endif
.PROXY               :=
ifneq ($(DOCKER_RUN),)
VARS                 := $(foreach E, $(shell printenv), -e "$(E)")
.PROXY               := docker-proxy-
ifeq ($(FORCE_DOCKER_BUILD),y)
sdist pkg-deb changelog: docker-pkg-deb-$(PKG_VENDOR)-$(PKG_DISTRIBUTION)
else
sdist pkg-deb changelog:
endif
	$(info Running target via Docker ($(ORG)/pkg-deb:$(PKG_VENDOR)-$(PKG_DISTRIBUTION)...))
	$(Q)$(call DOCKER_RUN,$(VARS),pkg-deb:$(PKG_VENDOR)-$(PKG_DISTRIBUTION)) $(MAKE) -e $@;
	$(Q)exit 0
test test-unit test-coverage test-lint: KRAFT_TARGET = kraft-dev
ifeq ($(FORCE_DOCKER_BUILD),y)
test test-unit test-coverage test-lint: docker-kraft
else
test test-unit test-coverage test-lint:
endif
	$(info Running target via Docker ($(ORG)/$(APP_NAME):latest-dev)...)
	$(Q)$(call DOCKER_RUN,$(VARS),kraft:latest-dev) $(MAKE) -e $@;
	$(Q)exit 0
endif


.PHONY: $(.PROXY)pkg-deb
ifneq (,$(findstring help,$(MAKECMDGOALS)))
$(.PROXY)pkg-deb:
	@echo "Usage: [DEBUILD=... DEBUILD_FLAGS=...] $(MAKE) $@                             "
	@echo "                                                                              "
	@echo "  Build a Debian-based packaging environment.  This target uses the Docker    "
	@echo "  environment defined within package/docker/Dockerfile.pkg-deb.  When run, a  "
	@echo "  changelog is also generated (in package/debian/changelog) and bundled with  "
	@echo "  the release.                                                                "
	@echo "                                                                              "
	@echo "Additional flags:                                                             "
	@echo "  DISTDIR           Output artifacts directory (default dist/).               "
	@echo "  APP_VERSION       Set the version of the release (Default: $(APP_VERSION)). "
	@echo "  PKG_NAME          Set the package name (Default: $(PKG_NAME)).              "
	@echo "  PKG_VENDOR        Set and use the Debian vendor (Default: $(PKG_VENDOR)).   "
	@echo "  PKG_DISTRIBUTION  Set and use a Debian distribution                         "
	@echo "                      (Default: $(PKG_DISTRIBUTION)).                         "
	@echo
else
$(.PROXY)pkg-deb: DEBUILD ?= debuild
$(.PROXY)pkg-deb: DEBUILD_FLAGS ?= --preserve-env -b -us -uc
$(.PROXY)pkg-deb: $(.PROXY)sdist $(.PROXY)changelog $(.PROXY)bump
$(.PROXY)pkg-deb:
	$(Q)$(MKDIR) -p $(DISTDIR)/build
	$(Q)$(TAR) -x -C $(DISTDIR)/build \
		--strip-components=1 \
		--exclude '*.egg-info' \
		-f $(DISTDIR)/$(PKG_NAME)-$(APP_VERSION).tar.gz
	$(Q)$(CP) -Rfv $(KRAFTDIR)/package/debian $(DISTDIR)/build
	$(Q)$(SED) -i \
		-re "1s/..UNRELEASED/~$(shell lsb_release -cs)) \
		    $(shell lsb_release -cs)/" $(DISTDIR)/build/debian/changelog
	$(Q)($(CD) $(DISTDIR)/build; $(DEBUILD) $(DEBUILD_FLAGS))
endif


.PHONY: $(.PROXY)sdist
ifneq (,$(findstring help,$(MAKECMDGOALS)))
$(.PROXY)sdist: no-help
else
$(.PROXY)sdist: SETUPPY_FLAGS ?= -d $(DISTDIR)
$(.PROXY)sdist: bump
	$(Q)$(SNAKE) setup.py sdist $(SETUPPY_FLAGS)
endif


.PHONY: bump
ifneq (,$(findstring help,$(MAKECMDGOALS)))
bump: no-help
else
bump:
	$(Q)$(SED) -i --regexp-extended "s/__version__[ ='0-9a-zA-Z\.\-]+/__version__ = '$(APP_VERSION)'/g" $(KRAFTDIR)/kraft/__init__.py
endif


.PHONY: release-commit
release-commit: COMMIT_MESSAGE ?= "$(APP_NAME) v$(APP_VERSION) released"
release-commit:
ifneq (,$(findstring help,$(MAKECMDGOALS)))
	@echo "Usage: [APP_VERSION=x.y.z-abc COMMIT_MESSAGE=\"...\"] $(MAKE) $@              "
	@echo "                                                                              "
	@echo "  Create a new release by creating a commit with a tag, with a default        "
	@echo "  message.  This will also call a git-hook which will run the linter (flake8)."
	@echo "  See .pre-commit-config.yaml for details.                                    "
	@echo "                                                                              "
	@echo "  The default COMMIT_MESSAGE is '$(COMMIT_MESSAGE)'.                          "
	@echo
else
	$(Q)$(GIT) add $(KRAFTDIR)/kraft/__init__.py $(KRAFTDIR)/Makefile $(KRAFTDIR)/package/debian/changelog
	$(Q)$(GIT) commit -s -m $(COMMIT_MESSAGE)
	$(Q)$(GIT) tag -a v$(APP_VERSION) -m $(COMMIT_MESSAGE)
endif


.PHONY: $(.PROXY)changelog
$(.PROXY)changelog: PREV_VERSION ?= $(shell git tag | sort -r | head -1 | awk '{split($$0, tags, "\n")} END {print tags[1]}')
$(.PROXY)changelog: DCH ?= dch
$(.PROXY)changelog: DCH_FLAGS ?=
ifeq ($(wildcard $(KRAFTDIR)/package/debian/changelog),)
$(.PROXY)changelog: DCH_FLAGS += --create
endif
$(.PROXY)changelog:
ifneq (,$(findstring help,$(MAKECMDGOALS)))
	@echo "Usage: [APP_VERSION=x.y.z.abc PKG_NAME=$(PKG_NAME)] $(MAKE) $@                "
	@echo "                                                                              "
	@echo "  Generate a changelog inside of package/debian/changelog based on all commits"
	@echo "  since the last release tag ($(PREV_VERSION)).                               "
	@echo
else ifeq ($(findstring $(APP_VERSION),$(shell head -1 $(KRAFTDIR)/package/debian/changelog)),)
	$(Q)$(CD) $(KRAFTDIR)/package && $(DCH) $(DCH_FLAGS) -M \
		-v "$(APP_VERSION)" \
		--package $(PKG_NAME) \
		--distribution UNRELEASED \
		"$(APP_NAME) v$(APP_VERSION) released"
	$(Q)$(GIT) log --format='%s' $(PREV_VERSION)..HEAD | sort -r | while read line; do \
		echo "Logging change: $$line"; \
		(cd $(KRAFTDIR)/package && $(DCH) -M -a "$$line"); \
	done;
endif


.PHONY: get-version
ifneq (,$(findstring help,$(MAKECMDGOALS)))
get-version: no-help
else
get-version:
	$(Q)echo $(APP_VERSION)
endif


.PHONY: install
ifneq (,$(findstring help,$(MAKECMDGOALS)))
install: no-help
else
install:
	$(Q)$(SNAKE) setup.py install
endif


.PHONY: $(.PROXY)test
.PHONY: $(.PROXY)test-all
ifneq (,$(findstring help,$(MAKECMDGOALS)))
test: no-help
test-all: no-help
else
$(.PROXY)test: $(.PROXY)test-all
$(.PROXY)test-all: \
	$(.PROXY)test-lint \
	$(.PROXY)test-pkg \
	$(.PROXY)test-unit \
	$(.PROXY)test-coverage \
	$(.PROXY)test-docker-pkg-deb-all
endif


.PHONY: $(.PROXY)test-lint
ifneq (,$(findstring help,$(MAKECMDGOALS)))
test-lint: no-help
else
$(.PROXY)test-lint: TOX ?= tox
$(.PROXY)test-lint: TOX_EXTRA ?= 
$(.PROXY)test-lint:
	$(Q)$(TOX) -e pre-commit $(TOX_EXTRA)
endif


.PHONY: test-pkg
ifneq (,$(findstring help,$(MAKECMDGOALS)))
test-pkg: no-help
else
test-pkg:
	$(Q)$(MAKE) test-docker-pkg-deb-all
endif


.PHONY: $(.PROXY)test-unit
ifneq (,$(findstring help,$(MAKECMDGOALS)))
test-unit: no-help
else
$(.PROXY)test-unit: PYTEST ?= pytest
$(.PROXY)test-unit:
	$(Q)$(PYTEST) -v # --conformity tests/acceptance/
endif


.PHONY: $(.PROXY)test-coverage
ifneq (,$(findstring help,$(MAKECMDGOALS)))
test-coverage: no-help
else
$(.PROXY)test-coverage: COVERAGE ?= coverage
$(.PROXY)test-coverage:
	$(Q)$(COVERAGE) run -m unittest discover
endif


.PHONY: clean
ifneq (,$(findstring help,$(MAKECMDGOALS)))
clean: no-help
else
clean:
	$(Q)$(RM) -Rfv $(DISTDIR)/build/*
endif


.PHONY: properclean
ifneq (,$(findstring help,$(MAKECMDGOALS)))
properclean: no-help
else
properclean:
	$(Q)$(RM) -Rfv $(DISTDIR)/*
endif


include $(KRAFTDIR)/package/docker/Makefile


.PHONY:
no-help:
	@echo "No help for target: $(strip $(subst help,,$(MAKECMDGOALS)))"
