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
from .instance import Instance
import os
import sys


class Project(object):
    '''A compose project is a group of containers read in from a config file.
    '''
    config = None
    instances = {}

    def __init__(self, filename=None, name=None, working_dir=None, env_file=None):

        self.set_filename(filename, working_dir)
        self.set_name(name)
        self.load()
        self.parse()
        self.env_file = env_file

    def __str__(self):
        return "(project:%s)" % self.name

    def __repr__(self):
        return self.__str__()

    def set_filename(self, filename, working_dir=None):
        '''set the filename to read the recipe from. If not provided, defaults
           to singularity-compose.yml

           Parameters
           ==========
           filename: the singularity-compose.yml file to use
        '''
        self.filename = filename or "singularity-compose.yml"

        # No working directory set, default to the location of compose file
        if working_dir is None:
            self.working_dir = os.path.dirname(self.filename)

    def set_name(self, name):
        '''set the filename to read the recipe from. If not provided, defaults
           to singularity-compose.yml
        '''
        pwd = os.path.basename(os.path.dirname(os.path.abspath(self.filename)))
        self.name = (name or pwd).lower()
        

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
                self.instances[name] = Instance(name, params)

            # Update volumes with volumes from
            for _, instance in self.instances.items():
                instance.set_volumes_from(self.instances)


# Build

    def build(self):
        '''given a loaded project, build associated containers (or pull).
        '''
        pass
