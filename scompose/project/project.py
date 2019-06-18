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

from scompose.logger import bot
from scompose.utils import read_yaml
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
        if self.config is not None:

            # Create each instance object
            for name in self.config.get('instances', []):
                params = self.config['instances'][name]

                # Validates params
                self.instances[name] = Instance(name=name,
                                                params=params,
                                                working_dir=self.working_dir)

            # Update volumes with volumes from
            for _, instance in self.instances.items():
                instance.set_volumes_from(self.instances)
            

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

    def create(self, names):
        '''call the create function, which defaults to the command instance.create()
        '''
        return self._create(names)

    def up(self, names):
        '''call the up function, instance.up(), which will build before if
           a container binary does not exist.
        '''
        return self._create(names, command="up")

    def _create(self, names, command="create"):
        '''create one or more instances. "Command" determines the sub function
           to call for the instance, which should be "create" or "up".
           If the user provide a list of names, use them, otherwise default
           to all instances.
          
           Parameters
           ==========
           names: the instance names to create
           command: one of "create" or "up"
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

                # If we get here, execute command and add to list
                getattr(instance, command)(self.working_dir)
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
