# Program arguments
BINARY_NAME    ?= tools
BINARY_UNIX    ?= $(BINARY_NAME)_unix
CONTAINER_NAME ?= unikraft/tools:latest

## Tools
DOCKER   ?= docker
TARGET   ?= binary
GO       ?= go
GOBUILD  ?= $(GO) build
GOCLEAN  ?= $(GO) clean
GOTEST   ?= $(GO) test
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
test:   
	$(GOTEST) -v ./...
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
# Cross compilation
build-linux:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GOBUILD) -o $(BINARY_UNIX) -v
