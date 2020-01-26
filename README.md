Unikraft Tools
==============================

Unikraft is an automated system for building specialized OSes and
unikernels tailored to the needs of specific applications. It is based
around the concept of small, modular libraries, each providing a part
of the functionality commonly found in an operating system (e.g.,
memory allocation, scheduling, filesystem support, network stack,
etc.).

This repo contains all tools related to Unikraft, and in particular
the kraft.py script which acts as a single point of entry for all
Unikraft operations, including the downloading, building and running
of Unikraft applications. You can run it without parameters to see its
help menu.

Note that the kraft.py, as well as this repo in general, is currently
under heavy development and should not yet be used unless you know
what you are doing. As things stabilize, we will update this file to
reflect this.

Read the [wiki](https://github.com/unikraft/tools/wiki) for
further information.
