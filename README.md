# kraft

To begin using [Unikraft](https://unikraft.org) you can use the
command-line utility `kraft`, which is a companion tool used for
defining, configuring, building, and running Unikraft applications.
With `kraft` you can seamlessly create a build environment for your
unikernel and painlessly manage dependencies for its build.

## Installing kraft

The `kraft` tool and Unikraft build system have a number of package requirements; please run the following command (on `apt-get`-based systems) to install the requirements:

    apt-get install -y --no-install-recommends build-essential libncurses-dev libyaml-dev flex git wget socat bison unzip uuid-runtime; 

To install `kraft` simply run:

    pip3 install git+https://github.com/unikraft/kraft.git
	
You can then type `kraft` to see its help menu

## Building an Application

The simplest way to get the sources for, build and run an application
is by running the following commands:

    kraft list
    kraft up -p PLATFORM -m ARCHITECTURE -a APP

For more information about that command type `kraft up -h`. For more information about `kraft` type ```kraft -h``` or read the documentation at [Unikraft's website](https://docs.unikraft.org). If you find any problems please [fill out an issue](https://github.com/unikraft/tools/issues/new/choose). Thank you!

## Contributing

Please refer to the [`README.md`](https://github.com/unikraft/unikraft/blob/master/README.md)
as well as the documentation in the [`doc/`](https://github.com/unikraft/unikraft/tree/master/doc)
subdirectory of the main Unikraft repository.
