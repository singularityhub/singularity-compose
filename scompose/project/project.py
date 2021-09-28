"""

Copyright (C) 2019-2021 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

from scompose.templates import get_template
from scompose.logger import bot
from scompose.utils import read_yaml, read_file, write_file
from spython.main import get_client
from .instance import Instance
from ipaddress import IPv4Network
import json
import os
import re
import subprocess
import sys


class Project(object):
    """A compose project is a group of containers read in from a config file."""

    config = None
    instances = {}

    def __init__(self, filename=None, name=None, env_file=None):

        self.set_filename(filename)
        self.set_name(name)
        self.load()
        self.parse()
        self.env_file = env_file
        self.client = get_client()
        self.running = self.get_already_running()

    # Names

    def __str__(self):
        return "(project:%s)" % self.name

    def __repr__(self):
        return self.__str__()

    def get_instance_names(self):
        """return a list of names, if a config file is loaded, and instances
        are defined.
        """
        names = []
        if self.instances is not None:
            names = list(self.instances.keys())

        return names

    def set_filename(self, filename):
        """set the filename to read the recipe from. If not provided, defaults
        to singularity-compose.yml. The working directory is set to
        be the directory name of the configuration file.

        Parameters
        ==========
        filename: the singularity-compose.yml file to use
        """
        self.filename = filename or "singularity-compose.yml"
        self.working_dir = os.path.dirname(os.path.abspath(self.filename))

    def set_name(self, name):
        """set the filename to read the recipe from. If not provided, defaults
        to singularity-compose.yml

        Parameters
        ==========
        name: if a customize name is provided, use it
        """
        pwd = os.path.basename(os.path.dirname(os.path.abspath(self.filename)))
        self.name = (name or pwd).lower()

    # Listing

    def ps(self):
        """ps will print a table of instances, including pids and names."""
        instance_names = self.get_instance_names()
        table = []
        for instance in self.client.instances(quiet=True, sudo=self.sudo):
            if instance.name in instance_names:
                image = os.path.basename(instance._image)
                ip_address = getattr(instance, "ip_address", None)
                table.append(
                    [instance.name.rjust(13), str(instance.pid), ip_address, image]
                )

        bot.custom(
            prefix="INSTANCES ",
            message="NAME         PID     IP              IMAGE",
            color="CYAN",
        )
        bot.table(table)

    def iter_instances(self, names):
        """yield instances one at a time. If an invalid name is given,
        exit with error.

        Parameters
        ==========
        names: the names of instances to yield. Must be valid
        """
        # Used to validate instance names
        instance_names = self.get_instance_names()

        for name in names:
            if name not in instance_names:
                bot.exit("%s is not a valid section name." % name)
            yield self.instances.get(name)

    def get_instance(self, name):
        """get a specifically named instance. We first check that the
        client has instances defined, and that the name we are looking
        for is also included. If not found, we return None.

        Parameters
        ==========
        names: the name of instances to get. Must be valid
        """
        instance = None
        if self.instances:
            if name in self.instances:
                instance = self.instances[name]
        return instance

    # Loading Functions

    def get_already_running(self):
        """Since a user can bring select instances up and down, we need to
        derive a list of already running instances to include
        """
        # Get list of existing instances to skip addresses
        instances = self.client.instances(quiet=True, return_json=True)

        # We can only get instances run by sudo if we have it
        if self.sudo:
            instances += self.client.instances(quiet=True, return_json=True, sudo=True)

        return {x["instance"]: x for x in instances}

    def load(self):
        """load a singularity-compose.yml recipe, and validate it."""

        if not os.path.exists(self.filename):
            bot.error("%s does not exist." % self.filename)
            sys.exit(1)

        try:
            self.config = read_yaml(self.filename, quiet=True)
        except:  # ParserError
            bot.exit("Cannot parse %s, invalid yaml." % self.filename)

    def parse(self):
        """parse a loaded config"""

        # If a port is defined, we need root.
        self.sudo = False

        if self.config is not None:

            # If any of config has ports, and no fakeroot, must use sudo
            for name in self.config.get("instances", []):
                params = self.config["instances"][name]
                start_options = params.get("start", {}).get("options", {})

                # If we have fakeroot, don't use sudo
                if (
                    "ports" in params
                    and "fakeroot" not in start_options
                    and "f" not in start_options
                ):
                    self.sudo = True

            # Create each instance object
            for name in self.config.get("instances", []):
                params = self.config["instances"][name]

                # Validates params
                self.instances[name] = Instance(
                    name=name,
                    params=params,
                    sudo=self.sudo,
                    working_dir=self.working_dir,
                )

            self.instances = self._sort_instances(self.instances)

            # Update volumes with volumes from
            for _, instance in self.instances.items():
                instance.set_volumes_from(self.instances)

    def _sort_instances(self, instances):
        """eventually reorder instances based on depends_on constraints"""
        sorted_instances = []
        for instance in self.instances:
            depends_on = self.instances[instance].params.get("depends_on", [])

            try:
                index = sorted_instances.index(instance)
            except ValueError:
                sorted_instances.append(instance)
                index = sorted_instances.index(instance)

            for dep in depends_on:
                if not dep in sorted_instances:
                    sorted_instances.insert(index, dep)

        return {k: self.instances[k] for k in sorted_instances}

    # Networking

    def get_ip_lookup(self, names, bridge="10.22.0.0/16"):
        """based on a bridge address that can serve other addresses (akin to
        a router, metaphorically, generate a pre-determined address for
        each container.

        Parameters
        ==========
        names: a list of names of instances to generate addresses for.
        bridge: the bridge address to derive them for.
        """

        host_iter = IPv4Network(bridge).hosts()
        lookup = {}

        # Don't include the gateway
        next(host_iter)

        # If an instance is already running, we want to include it
        all_names = set(self.config["instances"].keys())
        skip_addresses = [x["ip"] for name, x in self.running.items() if x["ip"]]

        # Only use addresses not currently in use
        for name in names:
            ip_address = str(next(host_iter))
            while ip_address in skip_addresses:
                ip_address = str(next(host_iter))
            lookup[name] = ip_address

        # Add instances that are already running
        for name in all_names:
            if name not in names and name in self.running:
                lookup[name] = self.running[name]["ip"]

        return lookup

    def get_bridge_address(self, name="sbr0"):
        """get the (named) bridge address on the host. It should be automatically
        created by Singularity over 3.0. This function currently is not used,
        but is left in case it's needed.

        Parameters
        ==========
        name: The default name of the Singularity bridge (sbr0)
        """
        command = ["ip", "-4", "--oneline", "address", "show", "up", name]
        result = self.client._run_command(
            command, return_result=True, quiet=True, sudo=self.sudo
        )["message"]
        bridge_address = re.match(".+ inet (?P<address>.+)/", result).groups()[0]
        return bridge_address

    def create_hosts(self, lookup):
        """create a hosts file to bind to all containers, where we define the
        correct hostnames to correspond with the ip addresses created.
        Note: This function is terrible. Singularity should easily expose
              these addresses. See issue here:
              https://github.com/sylabs/singularity/issues/3751

        Parameters
        ==========
        lookup: a lookup of ip addresses to assign the containers
        """
        hosts_file = os.path.join(self.working_dir, "etc.hosts")
        template = read_file(get_template("hosts"))

        # Add an entry for each instance hostname to see the others
        for name, ip_address in lookup.items():
            template = ["%s\t%s\n" % (ip_address, name)] + template

        # Add the host file to be mounted
        write_file(hosts_file, template)
        return hosts_file

    def generate_resolv_conf(self):
        """generate a resolv.conf file to bind to the containers.
        We use the template provided by scompose.
        """
        resolv_conf = os.path.join(self.working_dir, "resolv.conf")
        if not os.path.exists(resolv_conf):
            template = read_file(get_template("resolv.conf"))
            write_file(resolv_conf, template)
        return resolv_conf

    # Commands

    def shell(self, name):
        """if an instance exists, shell into it.

        Parameters
        ==========
        name: the name of the instance to shell into
        """
        instance = self.get_instance(name)
        if not instance:
            bot.exit("Cannot find %s, is it up?" % name)

        if instance.exists():
            self.client.shell(instance.instance.get_uri(), sudo=self.sudo)

    def run(self, name):
        """if an instance exists, run it.

        Parameters
        ==========
        name: the name of the instance to run
        """
        instance = self.get_instance(name)
        if not instance:
            bot.exit("Cannot find %s, is it up?" % name)

        if instance.exists():
            self.client.quiet = True
            result = self.client.run(
                instance.instance.get_uri(), sudo=self.sudo, return_result=True
            )

            if result["return_code"] != 0:
                bot.exit("Return code %s" % result["return_code"])
            print("".join([x for x in result["message"] if x]))

    def execute(self, name, commands):
        """if an instance exists, execute a command to it.

        Parameters
        ==========
        name: the name of the instance to exec to
        commands: a list of commands to issue
        """
        instance = self.get_instance(name)
        if not instance:
            bot.exit("Cannot find %s, is it up?" % name)

        if instance.exists():
            try:
                for line in self.client.execute(
                    instance.instance.get_uri(),
                    command=commands,
                    stream=True,
                    sudo=self.sudo,
                ):
                    print(line, end="")
            except subprocess.CalledProcessError:
                bot.exit("Command had non zero exit status.")

    # Logs

    def clear_logs(self, names):
        """clear_logs will remove all old error and output logs.

        Parameters
        ==========
        names: a list of names to clear logs for. We require the user
               to specifically name instances.
        """
        for instance in self.iter_instances(names):
            instance.clear_logs()

    def logs(self, names=None, tail=0):
        """logs will print logs to the screen.

        Parameters
        ==========
        names: a list of names of instances to show logs for.
               If not specified, show logs for all.
        """
        names = names or self.get_instance_names()
        for instance in self.iter_instances(names):
            instance.logs(tail=tail)

    # Config

    def view_config(self):
        """print a configuration file (in json) to the screen."""
        if self.config is not None:
            print(json.dumps(self.config, indent=4))

    # Down

    def down(self, names=None, timeout=None):
        """stop one or more instances. If no names are provided, bring them
        all down.

        Parameters
        ==========
        names: a list of names of instances to bring down. If not specified, we
        bring down all instances.
        """
        if not names:
            names = self.get_instance_names()
            # Ordered shutdown in case of depends_on
            names.reverse()

        for instance in self.iter_instances(names):
            instance.stop(timeout=timeout)

    # Create

    def create(
        self, names=None, writable_tmpfs=True, bridge="10.22.0.0/16", no_resolv=False
    ):

        """call the create function, which defaults to the command instance.create()"""
        return self._create(names, writable_tmpfs=writable_tmpfs, no_resolv=no_resolv)

    def up(
        self, names=None, writable_tmpfs=True, bridge="10.22.0.0/16", no_resolv=False,
    ):

        """call the up function, instance.up(), which will build before if
        a container binary does not exist.
        """
        return self._create(
            names, command="up", writable_tmpfs=writable_tmpfs, no_resolv=no_resolv,
        )

    def _create(
        self,
        names,
        command="create",
        writable_tmpfs=True,
        bridge="10.22.0.0/16",
        no_resolv=False,
    ):

        """create one or more instances. "Command" determines the sub function
        to call for the instance, which should be "create" or "up".
        If the user provide a list of names, use them, otherwise default
        to all instances.

        Parameters
        ==========
        names: the instance names to create
        command: one of "create" or "up"
        writable_tmpfs: if the instances should be given writable to tmp
        bridge: the bridge ip address to use for networking, and generating
                addresses for the individual containers.
                see /usr/local/etc/singularity/network/00_bridge.conflist
        no_resolv: if True, don't create and bind a resolv.conf with Google
                   nameservers.
        """
        # If no names provided, we create all
        names = names or self.get_instance_names()

        # Keep track of created instances to determine if we have circular dependency structure
        created = []
        circular_dep = False

        # Generate ip addresses for each
        lookup = self.get_ip_lookup(names, bridge)

        if not no_resolv:
            # Generate shared hosts file
            hosts_file = self.create_hosts(lookup)

        for instance in self.iter_instances(names):
            depends_on = instance.params.get("depends_on", [])
            for dep in depends_on:
                if dep not in created and dep not in self.running:
                    circular_dep = True

            # Generate a resolv.conf to bind to the container
            if not no_resolv:
                resolv = self.generate_resolv_conf()
                instance.volumes.append("%s:/etc/resolv.conf" % resolv)

                # Create a hosts file for the instance based, add as volume
                instance.volumes.append("%s:/etc/hosts" % hosts_file)

            # If we get here, execute command and add to list
            create_func = getattr(instance, command)
            create_func(
                working_dir=self.working_dir,
                writable_tmpfs=writable_tmpfs,
                ip_address=lookup[instance.name],
            )

            created.append(instance.name)

            # Run post create commands
            instance.run_post()

        if circular_dep:
            bot.exit("Unable to create all instances, possible circular dependency.")

    # Build

    def build(self, names=None):
        """given a loaded project, build associated containers (or pull)."""
        names = names or self.get_instance_names()
        for instance in self.iter_instances(names):
            instance.build(working_dir=self.working_dir)

            # Run post create commands
            instance.run_post()
