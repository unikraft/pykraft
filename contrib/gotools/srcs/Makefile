# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Gaulthier Gain <gaulthier.gain@uliege.be>
#
# Copyright (c) 2020, Université de Liège., ULiege. All rights reserved.
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

# Program arguments
BINARY_NAME    ?= gotools
BINARY_UNIX    ?= $(BINARY_NAME)_unix
CONTAINER_NAME ?= unikraft/gotools:latest

## Gotools
DOCKER   ?= docker
TARGET   ?= binary
GO       ?= go
GOBUILD  ?= $(GO) build
GOCLEAN  ?= $(GO) clean
GOGET    ?= $(GO) get

# Targets
all:	build
container:
	$(DOCKER) build \
		-t $(CONTAINER_NAME) \
		-f Dockerfile \
		--target=$(TARGET) \
		.
build: deps
	$(GOBUILD) -o $(BINARY_NAME)  -v
clean: 
	$(GOCLEAN)
	rm  -f  $(BINARY_NAME)
	rm  -f  $(BINARY_UNIX)
run:
	$(GOBUILD) -o $(BINARY_NAME) -v
	./$(BINARY_NAME)
deps:
	$(GOGET) github.com/fatih/color
	$(GOGET) github.com/akamensky/argparse
	$(GOGET) github.com/awalterschulze/gographviz
	$(GOGET) github.com/sergi/go-diff/...
# Cross compilation
build-linux:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GOBUILD) -o $(BINARY_UNIX) -v
