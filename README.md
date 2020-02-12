# `kraft` 

To begin using [Unikraft](https://unikraft.org>) you can use the command-line
utility `kraft`  which is a companion tool used for defining, configuring,
building, and running Unikraft unikernel applications.  With `kraft`, you can
create a build environment for your unikernel and manage dependencies for its
build.

```
Usage: kraft [OPTIONS] COMMAND [ARGS]...

Options:
  --version      Show the version and exit.
  -v, --verbose  Enables verbose mode.
  -h, --help     Show this message and exit.

Commands:
  build      Build the application.
  clean      Clean the application.
  configure  Configure the application.
  init       Initialize a new unikraft application.
  list       List architectures, platforms, libraries or applications.
  run        Run the application.
```

## Installation and documentation

* Full documentation is available on [Unikraft's website](https://docs.unikraft.org).
* Code repository for `kraft` is on [GitHub](https://github.com/unikraft/tools).
* If you find any problems please [fill out an issue](https://github.com/unikraft/tools/issues/new/choose). Thank you!

## Contributing

Please refer to the [`README.md`](https://github.com/unikraft/unikraft/blob/master/README.md)
as well as the documentation in the [`doc/`](https://github.com/unikraft/unikraft/tree/master/doc)
subdirectory of the main Unikraft repository.