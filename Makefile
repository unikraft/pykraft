
ORG?=unikraft

# Tools
DOCKER?=docker
PYTHON?=python

.PHONY: kraft
kraft:
	$(DOCKER) build \
		--tag $(ORG)/kraft:latest \
		--cache-from $(ORG)/kraft:latest \
		--file ./docker/Dockerfile.kraft \
		.

.PHONY: install
install:
	$(PYTHON) setup.py install

