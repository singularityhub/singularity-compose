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

        bot.custom(prefix="INSTANCES ", message="NAME PID     IMAGE",color="CYAN")
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
        '''load a singularity-compose.yml recipe, and validate it.'''

        if not os.path.exists(self.filename):
            log.error("%s does not exist." % self.filename)
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


    def create_hosts(self, name, depends_on):
        '''create a hosts file to bind to all containers, where we define the
           correct hostnames to correspond with the ip addresses created.

           Note: This function is terrible. Singularity should easily expose 
                 these addresses.
        '''
        template = read_file(get_template('hosts'))
        hosts_file = os.path.join(self.working_dir, 'etc.hosts.%s' % name)
        hosts_basename = os.path.basename(hosts_file)        

        for _, instance in self.instances.items():
           if instance.name in depends_on:   
               if self.sudo:
                   if instance.exists():
                       result = self.client.execute(image=instance.instance.get_uri(), 
                                                    command=['hostname', '-I'],
                                                    return_result=True,
                                                    sudo=self.sudo)

                       # Busybox won't have hostname -I
                       if result['return_code'] != 0:
                           cmd = "ip -4 --oneline address show up eth0"
                           result = self.client.execute(image=instance.instance.get_uri(), 
                                                        command=cmd,
                                                        return_result=True,
                                                        sudo=self.sudo)

                       ip_address = result['message'].strip('\n').strip()

                       # Clean up busybox output
                       if "inet" in ip_address:
                           ip_address = re.match('.+ inet (?P<address>.+)/', ip_address).groups()[0]
               else:
                   ip_address = '127.0.1.1'

               template = ['%s\t%s\n' % (ip_address, instance.name)] + template 
               instance.volumes.append('%s:/etc/hosts' % hosts_basename)
        write_file(hosts_file, template)


# Commands

    def shell(self, name):
        '''if an instance exists, shell into it.
        '''
        if self.instances:
            if name in self.instances:
                instance = self.instances[name]
                if instance.exists():
                    self.client.shell(instance.instance.get_uri())

# Config

    def view_config(self):
        '''print a configuration file (in json) to the screen.
        '''
        if self.config is not None:
            print(json.dumps(self.config, indent=4))

# Down

    def down(self, names):
        '''stop one or more instances. If no names are provided, bring them
           all down.
        '''
        # If no names provided, we bring all down
        if not names:
            names = self.get_instance_names()

        for instance in self.iter_instances(names):
            instance.stop()            


# Create

    def create(self, names, writable_tmpfs=False):
        '''call the create function, which defaults to the command instance.create()
        '''
        return self._create(names, writable_tmpfs=writable_tmpfs)

    def up(self, names, writable_tmpfs=False):
        '''call the up function, instance.up(), which will build before if
           a container binary does not exist.
        '''
        return self._create(names, command="up", writable_tmpfs=writable_tmpfs)

    def _create(self, names, command="create", writable_tmpfs=False):
        '''create one or more instances. "Command" determines the sub function
           to call for the instance, which should be "create" or "up".
           If the user provide a list of names, use them, otherwise default
           to all instances.
          
           Parameters
           ==========
           names: the instance names to create
           command: one of "create" or "up"
           writable_tmpfs: if the instances should be given writable to tmp
        '''
        # If no names provided, we create all
        if not names:
            names = self.get_instance_names()
         
        # Keep a count to determine if we have circular dependency structure
        created = []
        count = 0

        # First create those with no dependencies
        while names:
            
            for instance in self.iter_instances(names):

                # Ensure created, skip over if not
                for depends_on in instance.params.get('depends_on', []):
                    if depends_on not in created:
                        count += 1
                        continue

                # Create a hosts file for the instance based on depends
                self.create_hosts(instance.name, created)

                # If we get here, execute command and add to list
                getattr(instance, command)(self.working_dir, writable_tmpfs)
                created.append(instance.name)
                names.remove(instance.name) 

                # Possibly circular dependencies 
                if count >= 100:
                    bot.exit('Unable to create all instances, possible circular dependency.')

# Build

    def build(self):
        '''given a loaded project, build associated containers (or pull).
        '''
        # Loop through containers and build missing
        for name, instance in self.instances.items():
            instance.build(working_dir=self.working_dir)
