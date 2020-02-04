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
#
# THIS HEADER MAY NOT BE EXTRACTED OR MODIFIED IN ANY WAY.

import os
import json
import kconfiglib
import subprocess
import kraft.util as util
from kraft.errors import MisconfiguredUnikraftApp
from kraft.repo import Repo
from kraft.logger import logger
from json.decoder import JSONDecodeError
from kraft.component import KraftComponent

DEPS_JSON="deps.json"
DOT_CONFIG=".config"
DEFCONFIG="defconfig"
MAKEFILE_UK="Makefile.uk"

class UnikraftApp(object):

    ctx = None
    name = None
    core = (None, None)
    arch = (None, None)
    plat = (None, None)
    libs = {}
    kconf = None
    path = None
    template = None
    deps = {}

    # def __init__(self, name, unikraft, kconfig, archs=None, plats=None, libs=None, volumes=None, config_version=None):
    #     self.name = name
    #     self.unikraft = unikraft
    #     self.kconfig = kconfig
    #     self.archs = archs
    #     self.plats = plats or Platforms({})
    #     self.libs = libs or Libraries({})
    #     self.volumes = volumes or Volumes({})
    #     self.config_version = config_version

    @classmethod
    def from_config(cls, name, config_data):
        """Construct a Unikraft application from a config.Config object."""

        for lib in config_data.services:
            print(lib)        

        # volumes = Volumes.from_config(name, config_data)
        # project = cls(name, )



    # @classmethod
    # def from_config(cls, name, config_data, client, default_platform=None, extra_labels=None):
    #     """
    #     Construct a Project from a config.Config object.
    #     """
    #     extra_labels = extra_labels or []
    #     use_networking = (config_data.version and config_data.version != V1)
    #     networks = build_networks(name, config_data, client)
    #     project_networks = ProjectNetworks.from_services(
    #         config_data.services,
    #         networks,
    #         use_networking)
    #     volumes = ProjectVolumes.from_config(name, config_data, client)
    #     project = cls(name, [], client, project_networks, volumes, config_data.version)

    #     for service_dict in config_data.services:
    #         service_dict = dict(service_dict)
    #         if use_networking:
    #             service_networks = get_networks(service_dict, networks)
    #         else:
    #             service_networks = {}

    #         service_dict.pop('networks', None)
    #         links = project.get_links(service_dict)
    #         network_mode = project.get_network_mode(
    #             service_dict, list(service_networks.keys())
    #         )
    #         pid_mode = project.get_pid_mode(service_dict)
    #         volumes_from = get_volumes_from(project, service_dict)

    #         if config_data.version != V1:
    #             service_dict['volumes'] = [
    #                 volumes.namespace_spec(volume_spec)
    #                 for volume_spec in service_dict.get('volumes', [])
    #             ]

    #         secrets = get_secrets(
    #             service_dict['name'],
    #             service_dict.pop('secrets', None) or [],
    #             config_data.secrets)

    #         project.services.append(
    #             Service(
    #                 service_dict.pop('name'),
    #                 client=client,
    #                 project=name,
    #                 use_networking=use_networking,
    #                 networks=service_networks,
    #                 links=links,
    #                 network_mode=network_mode,
    #                 volumes_from=volumes_from,
    #                 secrets=secrets,
    #                 pid_mode=pid_mode,
    #                 platform=service_dict.pop('platform', None),
    #                 default_platform=default_platform,
    #                 extra_labels=extra_labels,
    #                 **service_dict)
    #         )

    #     return project


    def __init__(self,
        ctx=None,
        name=None,
        core=None,
        arch=None,
        plat=None,
        path=None,
        use_template=None,
        no_cache=False):
        """Initialize an appliance by manually specifying all attributes."""

        if name is not None:
            self.name = name

        if path is None:
            raise MisconfiguredUnikraftApp
        
        # We can only instantiate an appliance if we are given a path an some
        # context.  This is because context holds information about where
        # the repositories are held and thus the ability to cross-reference
        # these with the values that have been provided.
        elif ctx is not None:
            self.ctx = ctx
            self.path = path

            # If we can read from a deps.json file, we can populate anything
            # that is not passed to the constructor method.
            try:
                data = self.read_deps(path)

                if 'name' in data:
                    self.name = data['name']
                if 'core' in data:
                    self.core = (ctx.cache.repos(KraftComponent.CORE)['unikraft'], data['core'])
                if 'libs' in data:
                    libs = ctx.cache.repos(KraftComponent.LIB)
                    for lib in data['libs']:
                        self.add_lib(lib=libs[lib], version=data['libs'][lib])
                
            except CannotReadDepsJson:
                pass
            
            # Try reading from the template and set these values
            if use_template is not None and type(use_template) is Repo:
                self.template = use_template
                deps = self.read_deps(use_template.localdir)

                if 'libs' in deps:
                    libs = self.ctx.cache.repos(KraftComponent.LIB)
                    for lib in deps['libs']:
                        self.add_lib(lib=libs[lib], version=deps['libs'][lib])

            # Overwrite core if explicitly defined
            if core is not None:
                repo, version = core
                if type(repo) is Repo:
                    self.core = core
                
            # Overwrite arch if explicitly defined
            if arch is not None:
                repo, version = arch
                if type(repo) is Repo:
                    self.arch = arch

            # Overwrite plat if explicitly defined
            if plat is not None:
                repo, version = plat
                if type(repo) is Repo:
                    self.plat = plat
                
        # Context is everything
        else:
            raise MisconfiguredUnikraftApp

    def save(self, dry_run=False, force_overwrite=False):
        """Save configuration to disk at its working directory.  The save method
        is able to determine whether this is a first-time save and thus whether
        to copy over template files.  In addition to this, the save method uses
        """

        # If the template property has been set, cwe have been to told to write
        # this template to the path directory.
        if util.is_dir_empty(self.path) \
        or (util.is_dir_empty(self.path) is False and force_overwrite):

            logger.info("Writing changes using existing template: %s..." % self.template)

            # TODO:  If a file exists within the current self.path, prompt with 
            # a diff using $EDITOR and provide hunk selection.
            # if os.path.isdir(self.path):
            #     ...

            # Write .config file with default configuration
            # TODO:  This should also select any additional modes that were
            # passed by the init command
            if self.template is not None:
                util.recursively_copy(self.template.localdir, self.path, overwrite=force_overwrite, ignore=['.git'])

                # Create the .config file
                with open(os.path.join(self.path, DOT_CONFIG), 'w+') as dotconfig:
                    defconf = os.path.join(self.template.localdir, DEFCONFIG)
                    if os.path.isdir(defconf):
                        for conf in os.listdir(defconf):
                            if conf.endswith(DOT_CONFIG):
                                template = open(os.path.join(defconf, conf), 'r')
                                dotconfig.write(template.read())
                                template.close()
            else:
                # Write a blank .config file
                with open(os.path.join(self.path, DOT_CONFIG), 'w+') as dotconfig:
                    pass

        # Write our new deps.json file
        self.write_deps(self.path)

        # Are we saving to an existing application? (in the case of a template,
        # this will be true)
        # if KraftComponent.APP.valid_dir(self.path):
        #     logger.info("Saving %s..." % self.name)

        # else:
        #     logger.warning("Nothing to do for %s at %s" % (self.name, self.path))
        #     # TODO: Print changes

    def read_deps(self, localdir=None):
        """Read and parse the local deps.json file at a local directory."""

        if localdir is None:
            localdir = self.localdir

        if localdir is None:
            raise CannotReadDepsJson

        deps_json = os.path.join(localdir, DEPS_JSON)

        if os.path.exists(deps_json) is False:
            raise CannotReadDepsJson

        with open(deps_json) as f:
            try:
                data = json.load(f)
            except JSONDecodeError:
                raise CannotReadDepsJson

        # TODO: Perform validation of the file, e.g. testing wether the
        # specified core, platform, libraries are available at these release.
        return data

    def write_deps(self, localdir=None):
        """Write the local deps.json file at a local directory."""

        if localdir is None:
            localdir = self.localdir

        if localdir is None:
            raise CannotReadDepsJson

        deps_json = os.path.join(localdir, DEPS_JSON)

        with open(os.path.join(localdir, DEPS_JSON), 'w+') as outfile:
            outfile.write(self.toJSON())
            
    def write_config(self, localdir=None, write_makefile=False):
        """Write configuration files to the localdir."""
        pass

    def add_lib(self, lib=None, version=None):
        """Add a library to the unikraft appliance."""

        if isinstance(lib, Repo) and lib.name not in self.libs.keys():

            # Pick the latest version
            if version is None:
                version = lib.release

            self.libs[lib.name] = (lib, version)
    
    def make_cmd(self, extra=None):
        """Return a string with a correctly formatted make entrypoint for this
        application"""
        cmd = ['make', '-C', self.core[0].localdir, ('A=%s' % self.path)]
        paths = []

        for lib in self.libs:
            paths.append(self.libs[lib][0].localdir)

        cmd.append('L=%s' % ":".join(paths))

        if type(extra) is list:
            for i in extra:
                cmd.append(i)
        elif type(extra) is str:
            cmd.append(extra)

        return cmd

    def configure(self):
        """Configure a unikraft appliance."""
        self.checkout_versions()

        cmd = self.make_cmd(extra=[
            ('UK_DEFCONFIG=%s' % os.path.join(self.path, DOT_CONFIG)),
            'defconfig'
        ])
        
        util.execute(cmd)

        # TODO: Use Kconfig
        # self.kconf = kconfiglib.Kconfig(args.kconfig, suppress_traceback=True)
        # print(kconf.load_config(args.config))
        # print(kconf.write_config())
    
    def menuconfig(self):
        """Run the `make menuconfig` for interactive access to Unikraft
        application configuration."""
        self.checkout_versions()

        cmd = self.make_cmd('menuconfig')
        subprocess.run(cmd)
    
    def is_configured(self):
        """Determine if the application has been properly configured fo
        Unikraft."""

        if os.path.exists(os.path.join(self.path, DEPS_JSON)) is False:
            return False
        if os.path.exists(os.path.join(self.path, DOT_CONFIG)) is False:
            return False
        if os.path.exists(os.path.join(self.path, MAKEFILE_UK)) is False:
            return False

        return True
    
    def build(self, n_proc=None):
        """Checkout all the correct versions based on the current app instance
        and run the build command."""
        self.checkout_versions()

        cmd = self.make_cmd()

        if n_proc is not None:
            cmd.append('-j%s' % str(n_proc))

        util.execute(cmd)
    
    def clean(self, proper=False):
        """Clean the application."""
        # self.checkout_versions()

        if proper:
            cmd = self.make_cmd("properclean")
        # elif dist:
        #     cmd = self.make_cmd("distclean")
        else:
            cmd = self.make_cmd("clean")

        util.execute(cmd)
    
    def generate_makefile(self):
        pass
    
    def dump_sources(self):
        pass
    
    def checkout_versions(self):
        """Check out a particular version of the repository."""
        self.core[0].checkout(self.core[1])
        for lib in self.libs:
            self.libs[lib][0].checkout(self.libs[lib][1])

    def __str__(self):
        text = " App name....... %s\n" % self.name \
             + " Core........... %s\n" % self.core[1] \
             + " Libraries...... "
        for lib in self.libs:
            text += "%s %s\n%17s" % (self.libs[lib][0].name, self.libs[lib][1], " ")
        return text

    def toJSON(self):
        """Return a JSON serialized string of this object."""
        data = {
            "name": self.name,
            "core": self.core[1],
            "libs": {},
        }

        for lib in self.libs:
            repo, version = self.libs[lib]
            data['libs'][lib] = version

        return json.dumps(data, indent=4)