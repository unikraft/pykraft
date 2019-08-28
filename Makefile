# GO parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOCLEAN=$(GOCMD) clean
GOTEST=$(GOCMD) test
GOGET=$(GOCMD) get
BINARY_NAME=tools
BINARY_UNIX=$(BINARY_NAME)_unix

all:	build

build:  
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
