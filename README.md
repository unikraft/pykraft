# kraft

To begin using [Unikraft](https://unikraft.org) you can use the
command-line utility `kraft`, which is a companion tool used for
defining, configuring, building, and running Unikraft applications.
With `kraft` you can seamlessly create a build environment for your
unikernel and painlessly manage dependencies for its build.

## Installing kraft

The `kraft` tool and Unikraft build system have a number of package
requirements; please run the following command (on `apt-get`-based systems) to
install the requirements:

    apt-get install -y --no-install-recommends build-essential libncurses-dev libyaml-dev flex git wget socat bison unzip uuid-runtime python3-pip;

To install `kraft` simply run:

    pip3 install git+https://github.com/unikraft/kraft.git@staging

You can then type `kraft` to see its help menu

## Setting up kraft

The kraft app needs to additional steps to be fully configured. 

    kraft list update
    kraft list pull unikraft 

## Building an Application

The simplest way to get the sources for, build and run an application
is by running the following commands:

    kraft list update
    kraft up -t helloworld@staging ./my-first-unikernel

At present, Unikraft and kraft support the following applications:

* [C "hello world"](https://github.com/unikraft/app-helloworld) (`helloworld`);
* [C "http reply"](https://github.com/unikraft/app-httpreply) (`httpreply`);
* [C++ "hello world"](https://github.com/unikraft/app-helloworld-cpp) (`helloworld-cpp`);
* [Golang](https://github.com/unikraft/app-helloworld-go) (`helloworld-go`);
* [Python 3](https://github.com/unikraft/app-python3) (`python3`);
* [Micropython](https://github.com/unikraft/app-micropython) (`micropython`);
* [Ruby](https://github.com/unikraft/app-ruby) (`ruby`);
* [Lua](https://github.com/unikraft/app-lua) (`lua`);
* [Click Modular Router](https://github.com/unikraft/app-click) (`click`);
* [JavaScript (Duktape)](https://github.com/unikraft/app-duktape) (`duktape`);
* [Web Assembly Micro Runtime (WAMR)](https://github.com/unikraft/app-wamr) (`wamr`);
* [Redis](https://github.com/unikraft/app-redis) (`redis`);
* [Nginx](https://github.com/unikraft/app-nginx) (`nginx`);
* [SQLite](https://github.com/unikraft/app-sqlite) (`sqlite`);

For more information about that command type `kraft up -h`. For more information
about `kraft` type ```kraft -h``` or read the documentation at
[Unikraft's website](https://docs.unikraft.org). If you find any problems please
[fill out an issue](https://github.com/unikraft/tools/issues/new/choose). Thank
you!

## Contributing

Please refer to the [`README.md`](https://github.com/unikraft/unikraft/blob/master/README.md)
as well as the documentation in the [`doc/`](https://github.com/unikraft/unikraft/tree/master/doc)
subdirectory of the main Unikraft repository.
