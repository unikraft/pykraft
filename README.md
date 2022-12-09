# Project no longer maintained

| :warning: | To begin using [Unikraft](https://unikraft.org) please refer to [KraftKit](https://github.com/unikraft/kraftkit) which is the companion tool used for defining, configuring, building, and running Unikraft applications. |
|-|:-|
| | This project will be renamed to https://github.com/unikraft/pykraft.git on February 1st 2023. |

## pykraft: Python3 Bindings for Unikraft

The `pykraft` python library aids in building unikernels systematically.  It requires the following dependencies (for Debian-based systems):

    apt-get install -y --no-install-recommends build-essential libncurses-dev libyaml-dev flex git wget socat bison unzip uuid-runtime;

Note: Ubuntu 20.04 users may suffer from issue [#29](https://github.com/unikraft/kraft/issues/29) due to this [bug](https://bugs.launchpad.net/ubuntu/+source/socat/+bug/1883957) of `socat-1.7.3.3`. If you are using Ubuntu 20.04, please make sure to compile and install the latest version of `socat` retrieved from [this page](http://www.dest-unreach.org/socat/download/).

To install simply run:

    pip3 install git+https://github.com/unikraft/kraft.git@staging

## Building an Application

The simplest way to build a unikernel is to pass in an application directory to [`Application.from_workdir`](https://github.com/unikraft/kraft/blob/staging/kraft/app/app.py#L156):

```python
from kraft.app import Application

app = Application.from_workdir(workdir)

if not app.is_configured():
    app.configure()

app.fetch()
app.prepare()
app.build()
````

## License

Pykraft is part of the [Unikraft OSS Project](https://unikraft.org) and licensed under BSD-3-Clause.
