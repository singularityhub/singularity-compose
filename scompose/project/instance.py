"""

Copyright (C) 2019-2021 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

from scompose.logger import bot
from scompose.utils import get_userhome
from spython.main import get_client

import shlex
import os
import platform
import re


class Instance(object):
    """A section of a singularity-compose.yml, typically includes an image
    name, volumes, build directory, and any ports or environment variables
    relevant to the instance.

    Parameters
    ==========
    name: should correspond to the section name for the instance.
    working_dir: should be the projects working directory, where a folder
                 named according to "name" is created for the image binary.
    params: all of the parameters defined in the configuration.
    """

    def __init__(self, name, working_dir, sudo=False, params=None):

        if not params:
            params = {}

        self.image = None
        self.recipe = None
        self.instance = None
        self.sudo = sudo
        self.set_name(name, params)

        # Start includes networking args and command
        self.set_start(params)

        # Exec and run are done after a start, if provided
        self.set_exec(params)
        self.set_run(params)

        self.set_context(params)
        self.set_volumes(params)
        self.set_network(params)
        self.set_ports(params)
        self.params = params
        self.client = get_client()
        self.working_dir = working_dir

        # If the instance exists, instantiate it
        self.get()

    def __str__(self):
        return "(instance:%s)" % self.name

    def __repr__(self):
        return self.__str__()

    def set_name(self, name, params):
        """set the instance name. First priority goes to name  parameter, then
        to name in file

        Parameters
        ==========
        name: the name of the instance, the first field in the config file.
        params: dictionary of key, value parameters
        """
        self.name = params.get("name", name)

    @property
    def uri(self):
        return "instance://%s" % self.name

    def set_context(self, params):
        """set and validate parameters from the singularity-compose.yml,
        including build (context and recipe). We don't pull or create
        anything here, but rather just validate that the sections
        are provided and files exist.
        """

        # build the container on the host from a context
        if "build" in params:

            if "context" not in params["build"]:
                bot.exit("build.context section missing for %s" % self.name)

            # The user provided a build context
            self.context = params["build"]["context"]

            # The context folder must exist
            if not os.path.exists(self.context):
                bot.exit("build.context %s does not exist." % self.context)

            self.recipe = params["build"].get("recipe", "Singularity")

            # The recipe must exist in the context folder
            if not os.path.exists(os.path.join(self.context, self.recipe)):
                bot.exit("%s does not exist in %s" % (self.recipe, self.context))

        # An image can be pulled instead
        elif "image" in params:

            # If going to pull an image, the context is a folder of same name
            self.context = self.name

            # Image is validated when it needs to be used / pulled
            self.image = params["image"]

        # We are required to have build OR image
        else:
            bot.exit("build or image must be defined for %s" % self.name)

    # Volumes and Ports

    def set_volumes(self, params):
        """set volumes from the recipe"""
        self.volumes = params.get("volumes", [])
        self._volumes_from = params.get("volumes_from", [])

    def set_volumes_from(self, instances):
        """volumes from is called after all instances are read in, and
        then volumes can be mapped (and shared) with both containers.
        with Docker, this is done with isolation, but for Singularity
        we will try sharing a bind on the host.

        Parameters
        ==========
        instances: a list of other instances to get volumes from
        """
        for name in self._volumes_from:
            if name not in instances:
                bot.exit("%s not in config is specified to get volumes from." % name)
            for volume in instances[name].volumes:
                if volume not in self.volumes:
                    self.volumes.append(volume)

    def set_network(self, params):
        """set network from the recipe to be used"""
        self.network = params.get("network", {})

        # if not specified, set the default value for the property
        for key in ["enable", "allocate_ip"]:
            self.network[key] = self.network.get(key, True)

    def set_ports(self, params):
        """set ports from the recipe to be used"""
        self.ports = params.get("ports", [])

    # Commands

    def set_start(self, params):
        """set arguments to the startscript"""
        start = params.get("start", {})
        self.args = start.get("args", "")
        self.start_opts = [
            "--%s" % opt if len(opt) > 1 else "-%s" % opt
            for opt in start.get("options", [])
        ]

    def set_exec(self, params):
        """set arguments for exec"""
        exec_group = params.get("exec", {})
        self.exec_args = exec_group.get("command", "")
        if "|" in self.exec_args:
            bot.exit("Pipes are not currently supported.")
        self.exec_opts = self._get_command_opts(exec_group.get("options", []))

    def set_run(self, params):
        """set arguments for run"""
        run_group = params.get("run", {}) or {}
        self.run_args = run_group.get("args")
        if self.run_args and "|" in self.run_args:
            bot.exit("Pipes are not currently supported.")
        self.run_opts = self._get_command_opts(run_group.get("options", []))

    def _get_command_opts(self, group):
        """Given a string of arguments or options, parse into a list with
        proper flags added.
        """
        return ["--%s" % opt if len(opt) > 1 else "-%s" % opt for opt in group]

    def _get_network_commands(self, ip_address=None):
        """take a list of ports, return the list of --network-args to
        ensure they are bound correctly.
        """
        ports = self.start_opts + ["--net"]

        # Fakeroot means not needing sudo
        fakeroot = "--fakeroot" in self.start_opts or "-f" in self.start_opts

        # If not sudo or fakeroot, we need --network none
        if not self.sudo and not fakeroot:
            ports += ["--network", "none"]

        for pair in self.ports:
            ports += ["--network-args", '"portmap=%s/tcp"' % pair]

        # Ask for a custom ip address
        if ip_address is not None and self.network["allocate_ip"]:
            ports += ["--network-args", '"IP=%s"' % ip_address]

        return ports

    def _get_bind_commands(self):
        """take a list of volumes, and return the bind commands for Singularity"""
        binds = []
        for volume in self.volumes:
            src, dest = volume.split(":")

            # First try, assume file in root folder
            if not os.path.exists(os.path.abspath(src)):
                if os.path.exists(os.path.join(self.working_dir, src)):
                    src = os.path.join(self.working_dir, src)
                elif os.path.exists(os.path.join(self.working_dir, self.name, src)):
                    src = os.path.join(self.working_dir, self.name, src)
                else:
                    bot.exit("bind source file %s does not exist" % src)

            # For the src, ensure that it exists
            bind = "%s:%s" % (os.path.abspath(src), os.path.abspath(dest))
            binds += ["--bind", bind]
        return binds

    def run_post(self):
        """run post create commands. Can be added to an instance definition
         either to run a command directly, or execute a script. The path
         is assumed to be on the host.

        post:
          command: ["mkdir", "-p", "./images/_upload/{0..9}"]

        OR

        post:
          command: "mkdir -p ./images/_upload/{0..9}"
        """
        if "post" in self.params:
            if "command" in self.params["post"]:
                command = self.params["post"]["command"]

                # Command must be a list
                if not isinstance(command, list):
                    command = shlex.split(command)

                # Capture the return code
                response = self.client._run_command(
                    command, quiet=True, return_result=True
                )
                # If debug on, show output
                bot.debug("".join(response["message"]))

                # Alert the user if there is an error
                if response["return_code"] != 0:
                    bot.error("".join(response["message"]))
                    bot.exit("Return code %s, exiting." % response["return_code"])

    # Image

    def get_image(self):
        """get the associated instance image name, to be built if it doesn't
        exit. It can either be defined at the config from self.image, or
        ultimately generated via a pull from a uri.
        """
        # If the user gave a direct image
        if self.image is not None:
            if os.path.exists(self.image):
                return self.image

        context = os.path.abspath(self.context)

        # if the context directory doesn't exist, create it
        if not os.path.exists(context):
            bot.info("Creating image context folder for %s" % self.name)
            os.mkdir(context)

        # The sif binary should have a predictible name
        return os.path.join(context, "%s.sif" % self.name)

    # Build

    def build(self, working_dir):
        """build an image if called for based on having a recipe and context.
        Otherwise, pull a container uri to the instance workspace.
        """
        sif_binary = self.get_image()

        # If the final image already exists, don't continue
        if os.path.exists(sif_binary):
            return

        # Case 1: Given an image
        if self.image is not None:
            if not os.path.exists(self.image):

                # Can we pull it?
                if re.search("(docker|library|shub|http?s)[://]", self.image):
                    bot.info("Pulling %s" % self.image)
                    self.client.pull(self.image, name=sif_binary)

                else:
                    bot.exit(
                        "%s is an invalid unique resource identifier." % self.image
                    )

        # Case 2: Given a recipe
        elif self.recipe is not None:

            # Change directory to the context
            context = os.path.abspath(self.context)
            os.chdir(context)

            # The recipe is expected to exist in the context folder
            if not os.path.exists(self.recipe):
                bot.exit("%s not found for build" % self.recipe)

            # This will likely require sudo, unless --remote or --fakeroot in options
            try:
                options = self.get_build_options()

                # If remote or fakeroot included, don't need sudo
                sudo = not ("--fakeroot" in options or "--remote" in options)

                bot.info("Building %s" % self.name)

                _, stream = self.client.build(
                    image=sif_binary,
                    recipe=self.recipe,
                    options=options,
                    sudo=sudo,
                    stream=True,
                )

                for line in stream:
                    print(line)

            except:
                build = "sudo singularity build %s %s" % (
                    os.path.basename(sif_binary),
                    self.recipe,
                )

                bot.warning("Issue building container, try: %s" % build)

            # Change back to provided working directory
            os.chdir(working_dir)

        else:
            bot.exit("neither image and build defined for %s" % self.name)

    def get_build_options(self):
        """'get build options will parse through params, and return build
        options (if they exist)
        """
        options = []

        if "build" in self.params:
            if "options" in self.params["build"]:
                for option in self.params["build"]["options"]:

                    # if the option is a string, it's a boolean flag
                    if isinstance(option, str):
                        options.append("--%s" % option)

                    # Otherwise, the user set a boolean with a value or an arg
                    elif isinstance(option, dict):
                        for key, val in option.items():
                            if val is True:
                                options.append("--%s" % key)
                            elif val is False:
                                continue
                            else:
                                options += ["--%s" % key, val]

        return options

    # State

    def exists(self):
        """return boolean if an instance exists. We do this by way of listing
        instances, and so the calling user is important.
        """
        instances = [x.name for x in self.client.instances(quiet=True, sudo=self.sudo)]
        return self.name in instances

    def get(self):
        """If an instance exists, add to self.instance"""
        for instance in self.client.instances(quiet=True, sudo=self.sudo):
            if instance.name == self.name:
                self.instance = instance
                break

    def stop(self, timeout=None):
        """delete the instance, if it exists. Singularity doesn't have delete
        or remove commands, everyting is a stop.
        """
        if self.instance:
            bot.info("Stopping %s" % self)
            self.instance.stop(sudo=self.sudo, timeout=timeout)
            self.instance = None

    # Networking

    def get_address(self):
        """get the bridge address of an image. If it's busybox, we can't use
        hostname -I.
        """
        ip_address = None
        if self.sudo:
            if self.exists():
                result = self.client.execute(
                    image=self.instance.get_uri(),
                    command=["hostname", "-I"],
                    return_result=True,
                    quiet=True,
                    sudo=self.sudo,
                )

                # Busybox won't have hostname -I
                if result["return_code"] != 0:
                    cmd = "ip -4 --oneline address show up eth0"
                    result = self.client.execute(
                        image=self.instance.get_uri(),
                        command=cmd,
                        return_result=True,
                        quiet=True,
                        sudo=self.sudo,
                    )

                ip_address = result["message"].strip("\n").strip()
                if "inet" in ip_address:
                    ip_address = re.match(
                        ".+ inet (?P<address>.+)/", ip_address
                    ).groups()[0]
        else:
            ip_address = "127.0.1.1"

        return ip_address

    # Logs

    def clear_logs(self):
        """delete logs for an instance, if they exist."""
        log_folder = self._get_log_folder()

        for ext in ["out", "err"]:
            logfile = os.path.join(log_folder, "%s.%s" % (self.name, ext.lower()))

            # Use Try/catch to account for not existing.
            try:
                if not self.sudo:
                    self.client._run_command(["rm", logfile], quiet=True)
                    self.client._run_command(["touch", logfile], quiet=True)
                else:
                    self.client._run_command(["sudo", "rm", logfile], quiet=True)
                    self.client._run_command(["sudo", "touch", logfile], quiet=True)
            except:
                pass

    def _get_log_folder(self):
        """get a log folder that includes a user, home, and host"""
        home = get_userhome()
        user = os.path.basename(home)

        if self.sudo:
            home = "/root"
            user = "root"

        # Hostname
        hostname = platform.node()
        return os.path.join(home, ".singularity", "instances", "logs", hostname, user)

    def logs(self, tail=0):
        """show logs for an instance"""

        log_folder = self._get_log_folder()

        for ext in ["OUT", "ERR"]:
            logfile = os.path.join(log_folder, "%s.%s" % (self.name, ext.lower()))

            # Use Try/catch to account for not existing.
            try:
                result = self.client._run_command(
                    ["cat", logfile], quiet=True, sudo=self.sudo
                )
                if result:
                    # If the user only wants to see certain number
                    if tail > 0:
                        result = "\n".join(result.split("\n")[-tail:])
                    bot.custom(prefix=self.name, message=ext, color="CYAN")
                    print(result)
                    bot.newline()

            except:
                pass

    # Create and Delete

    def up(self, working_dir, ip_address=None, writable_tmpfs=False):
        """up is the same as create, but like Docker, we build / pull instances
        first.
        """
        image = self.get_image() or ""

        # Do a build if necessary
        if not os.path.exists(image):
            self.build(working_dir)
        self.create(writable_tmpfs=writable_tmpfs, ip_address=ip_address)

    def create(self, ip_address=None, sudo=False, writable_tmpfs=False):
        """create an instance, if it doesn't exist."""
        image = self.get_image()

        # Case 1: No build context or image defined
        if image is None:
            bot.exit(
                "Please define an image or build context for instance %s" % self.name
            )

        # Case 2: Image not built.
        if not os.path.exists(image):
            bot.exit("Image %s not found, please run build first." % image)

        # Finally, create the instance
        if not self.exists():

            bot.info("Creating %s" % self.name)

            # Command options
            options = []

            # Volumes
            options += self._get_bind_commands()

            # Network configuration + Ports
            if self.network["enable"]:
                options += self._get_network_commands(ip_address)

            # Hostname
            options += ["--hostname", self.name]

            # Writable Temporary Directory
            if writable_tmpfs:
                options += ["--writable-tmpfs"]

            # Show the command to the user
            commands = "%s %s %s %s" % (" ".join(options), image, self.name, self.args)
            bot.debug("singularity instance start %s" % commands)

            self.instance = self.client.instance(
                name=self.name,
                sudo=self.sudo,
                options=options,
                image=image,
                args=self.args,
            )

            # If the user has exec defined, exec to it
            if self.exec_args:

                # Show the command to the user
                commands = "%s %s %s" % (
                    " ".join(self.exec_opts),
                    self.uri,
                    self.exec_args,
                )
                bot.debug("singularity exec %s" % commands)

                for line in self.client.execute(
                    image=self.instance,
                    command=self.exec_args,
                    sudo=self.sudo,
                    stream=True,
                    options=self.exec_opts,
                ):
                    print(line)

            # If the user has run defined, finish with the run
            if "run" in self.params:

                # Show the command to the user
                commands = "%s %s %s" % (
                    " ".join(self.run_opts),
                    self.uri,
                    self.run_args or "",
                )
                bot.debug("singularity run %s" % commands)

                for line in self.client.run(
                    image=self.instance,
                    args=self.run_args,
                    sudo=self.sudo,
                    stream=True,
                    options=self.run_opts,
                ):
                    print(line)
