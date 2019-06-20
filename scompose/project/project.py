'''

Copyright (C) 2019 Vanessa Sochat.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''

from scompose.templates import get_template
from scompose.logger import bot
from scompose.utils import (
    read_yaml,
    read_file,
    write_file
)
from spython.main import get_client
from .instance import Instance
from ipaddress import IPv4Network
import json
import os
import re
import sys


class Project(object):
    '''A compose project is a group of containers read in from a config file.
    '''
    config = None
    instances = {}

    def __init__(self, filename=None, name=None, env_file=None):

        self.set_filename(filename)
        self.set_name(name)
        self.load()
        self.parse()
        self.env_file = env_file
        self.client = get_client()

# Names

    def __str__(self):
        return "(project:%s)" % self.name

    def __repr__(self):
        return self.__str__()

    def get_instance_names(self):
        '''return a list of names, if a config file is loaded, and instances
           are defined.
        '''
        names = []
        if self.config is not None:
            if "instances" in self.config:
                names = list(self.config['instances'].keys())
        return names


    def set_filename(self, filename):
        '''set the filename to read the recipe from. If not provided, defaults
           to singularity-compose.yml. The working directory is set to
           be the directory name of the configuration file.

           Parameters
           ==========
           filename: the singularity-compose.yml file to use
        '''
        self.filename = filename or "singularity-compose.yml"
        self.working_dir = os.path.dirname(os.path.abspath(self.filename))

    def set_name(self, name):
        '''set the filename to read the recipe from. If not provided, defaults
           to singularity-compose.yml

           Parameters
           ==========
           name: if a customize name is provided, use it
        '''
        pwd = os.path.basename(os.path.dirname(os.path.abspath(self.filename)))
        self.name = (name or pwd).lower()


# Listing

    def ps(self):
        '''ps will print a table of instances, including pids and names.
        '''
        instance_names = self.get_instance_names()
        table = []
        for instance in self.client.instances(quiet=True, sudo=self.sudo):
            if instance.name in instance_names:
                image = os.path.basename(instance._image)
                table.append([instance.name.rjust(12), 
                              instance.pid, 
                              image])

        bot.custom(prefix="INSTANCES ",
                   message="NAME PID     IMAGE", 
                   color="CYAN")

        bot.table(table)
        
    def iter_instances(self, names):
        '''yield instances one at a time. If an invalid name is given,
           exit with error.

           Parameters
           ==========
           names: the names of instances to yield. Must be valid
        '''
        # Used to validate instance names
        instance_names = self.get_instance_names()

        for name in names:
            if name not in instance_names:
                bot.exit('%s is not a valid section name.' % name)
            yield self.instances.get(name)
        

# Loading Functions
  
    def load(self):
        '''load a singularity-compose.yml recipe, and validate it.
        '''

        if not os.path.exists(self.filename):
            bot.error("%s does not exist." % self.filename)
            sys.exit(1)
 
        try:
            self.config = read_yaml(self.filename, quiet=True)
        except: # ParserError
            bot.exit('Cannot parse %s, invalid yaml.' % self.filename)


    def parse(self):
        '''parse a loaded config'''

        # If a port is defined, we need root.
        self.sudo = False
        
        if self.config is not None:

            # If any of config has ports, must use sudo for networking
            for name in self.config.get('instances', []):
                params = self.config['instances'][name]
                if "ports" in params:
                    self.sudo = True

            # Create each instance object
            for name in self.config.get('instances', []):
                params = self.config['instances'][name]

                # Validates params
                self.instances[name] = Instance(name=name,
                                                params=params,
                                                sudo=self.sudo,
                                                working_dir=self.working_dir)

            # Update volumes with volumes from
            for _, instance in self.instances.items():
                instance.set_volumes_from(self.instances)


# Networking

    def get_ip_lookup(self, names, bridge="10.22.0.0/16"):
        '''based on a bridge address that can serve other addresses (akin to
           a router, metaphorically, generate a pre-determined address for
           each container.

           Parameters
           ==========
           names: a list of names of instances to generate addresses for. 
           bridge: the bridge address to derive them for.
        '''
        
        host_iter = IPv4Network(bridge).hosts()
        lookup = {}
 
        # Don't include the gateway
        next(host_iter)

        for name in names:
            lookup[name] = str(next(host_iter))

        return lookup


    def get_bridge_address(self, name='sbr0'):
        '''get the (named) bridge address on the host. It should be automatically
           created by Singularity over 3.0. This function currently is not used,
           but is left in case it's needed.

           Parameters
           ==========
           name: The default name of the Singularity bridge (sbr0)
        '''
        command = ["ip", "-4", "--oneline", "address", "show", "up", name]
        result = self.client._run_command(command,
                                          return_result=True,
                                          quiet=True,
                                          sudo=self.sudo)['message']
        bridge_address = re.match('.+ inet (?P<address>.+)/', result).groups()[0]
        return bridge_address


    def create_hosts(self, lookup):
        '''create a hosts file to bind to all containers, where we define the
           correct hostnames to correspond with the ip addresses created.
           Note: This function is terrible. Singularity should easily expose 
                 these addresses. See issue here:
                 https://github.com/sylabs/singularity/issues/3751

           Parameters
           ==========
           lookup: a lookup of ip addresses to assign the containers
        '''
        template = read_file(get_template('hosts'))
        hosts_file = os.path.join(self.working_dir, 'etc.hosts')

        # Add an entry for each instance hostname to see the others
        for name, ip_address in lookup.items():
            template = ['%s\t%s\n' % (ip_address, name)] + template

        # Add the host file to be mounted
        write_file(hosts_file, template)
        return hosts_file
 

# Commands

    def shell(self, name):
        '''if an instance exists, shell into it.

           Parameters
           ==========
           name: the name of the instance to shell into
        '''
        if self.instances:
            if name in self.instances:
                instance = self.instances[name]
                if instance.exists():
                    self.client.shell(instance.instance.get_uri(), sudo=self.sudo)


    def execute(self, name, commands):
        '''if an instance exists, execute a command to it.

           Parameters
           ==========
           name: the name of the instance to exec to
           commands: a list of commands to issue
        '''
        if self.instances:
            if name in self.instances:
                instance = self.instances[name]
                if instance.exists():
                    for line in self.client.execute(instance.instance.get_uri(), 
                                                    command=commands,
                                                    stream=True,
                                                    sudo=self.sudo):
                        print(line, end='')

# Logs

    def clear_logs(self, names):
        '''clear_logs will remove all old error and output logs.

           Parameters
           ==========
           names: a list of names to clear logs for. We require the user
                  to specifically name instances.
        '''
        for instance in self.iter_instances(names):
            instance.clear_logs()


    def logs(self, names=None, tail=0):
        '''logs will print logs to the screen.

           Parameters
           ==========
           names: a list of names of instances to show logs for. 
                  If not specified, show logs for all.
        '''
        names = names or self.get_instance_names()
        for instance in self.iter_instances(names):
            instance.logs(tail=tail)

# Config

    def view_config(self):
        '''print a configuration file (in json) to the screen.
        '''
        if self.config is not None:
            print(json.dumps(self.config, indent=4))

# Down

    def down(self, names=None):
        '''stop one or more instances. If no names are provided, bring them
           all down.

           Parameters
           ==========
           names: a list of names of instances to bring down. If not specified, we
           bring down all instances.
        '''
        names = names or self.get_instance_names()
        for instance in self.iter_instances(names):
            instance.stop()


# Create

    def create(self, names=None, writable_tmpfs=True, bridge="10.22.0.0/16"):
        '''call the create function, which defaults to the command instance.create()
        '''
        return self._create(names, writable_tmpfs=writable_tmpfs)

    def up(self, names=None, writable_tmpfs=True, bridge="10.22.0.0/16"):
        '''call the up function, instance.up(), which will build before if
           a container binary does not exist.
        '''
        return self._create(names, command="up", writable_tmpfs=writable_tmpfs)

    def _create(self, 
                names, 
                command="create",
                writable_tmpfs=True,
                bridge="10.22.0.0/16"):

        '''create one or more instances. "Command" determines the sub function
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
        '''
        # If no names provided, we create all
        names = names or self.get_instance_names()
         
        # Keep a count to determine if we have circular dependency structure
        created = []
        count = 0

        # Generate ip addresses for each
        lookup = self.get_ip_lookup(names, bridge)

        # Generate shared hosts file
        hosts_file = self.create_hosts(lookup)

        # First create those with no dependencies
        while names:
            
            for instance in self.iter_instances(names):

                # Flag to indicated create
                do_create = True

                # Ensure created, skip over if not
                depends_on = instance.params.get('depends_on', [])
                for depends_on in depends_on:
                    if depends_on not in created:
                        count += 1
                        do_create = False

                if do_create:

                    instance.volumes.append('%s:/etc/hosts' % hosts_file)

                    # Create a hosts file for the instance based, add as volume

                    # If we get here, execute command and add to list
                    create_func = getattr(instance, command)
                    create_func(working_dir=self.working_dir,
                                writable_tmpfs=writable_tmpfs,
                                ip_address=lookup[instance.name])

                    created.append(instance.name)
                    names.remove(instance.name) 
                 
                    # Run post create commands
                    instance.run_post()

                # Possibly circular dependencies 
                if count >= 100:
                    bot.exit('Unable to create all instances, possible circular dependency.')


# Build


    def build(self, names=None):
        '''given a loaded project, build associated containers (or pull).
        '''
        names = names or self.get_instance_names()
        for instance in self.iter_instances(names):        
            instance.build(working_dir=self.working_dir)

            # Run post create commands
            instance.run_post()
