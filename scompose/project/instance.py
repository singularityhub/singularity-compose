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
import shlex as _shlex
import os
import sys


class Instance(object):
    '''A section of a singularity-compose.yml, typically includes an image
       name, volumes, build directory, and any ports or environment variables
       relevant to the instance.
    '''
    def __init__(self, name, params={}):

        self.image = None
        self.recipe = None
        self.set_name(name, params)
        self.set_context(params)
        self.set_volumes(params)
        self.set_startscript(params)
        self.set_entrypoint(params)

    def __str__(self):
        return "(instance:%s)" % self.name

    def __repr__(self):
        return self.__str__()

    def set_name(self, name, params):
        '''set the instance name. First priority goes to name  parameter, then 
           to name in file

           Parameters
           ==========
           name: the name of the instance, the first field in the config file.
           params: dictionary of key, value parameters
        '''
        self.name = params.get('name', name)
        
    def set_entrypoint(self, params, default="/bin/bash"):
        '''set the entrypoint for the container, or default to /bin/bash
        '''
        self._set_script('entrypoint', params, default)

    def set_startscript(self, params, default="/bin/bash"):
        '''set the startscript for the container
        '''
        self._set_script('startscript', params, default)

    def _set_script(self, name, params, default):
        '''set a script (entrypoint or startscript) and fall back on a default

           Parameters
           ==========
           name: the name of the key to look up (startscript or entrypoint)
           params: dictionary for instance parameters
           default: the default value to set if not defined in params
        '''
        script = params.get(name, default)
        commands = _shlex.split(' '.join(script))
        setattr(self, name, commands)

    def set_context(self, params):
        '''set and validate parameters from the singularity-compose.yml,
           including build (context and recipe). We don't pull or create
           anything here, but rather just validate that the sections
           are provided and files exist.
        '''

        # build the container on the host from a context
        if "build" in params:
            
            if "context" not in params['build']:
                bot.exit("build.context section missing for %s" % self.name)

            # The user provided a build context
            self.context = params['build']['context']

            # The context folder must exist
            if not os.path.exists(self.context):
                bot.exit("build.context %s does not exist." % self.context)
 
            recipe = params['build'].get('recipe', 'Singularity')
            self.recipe = os.path.join(self.context, recipe)

            # The recipe must exist in the context folder
            if not os.path.exists(self.recipe):
                bot.exit("%s does not exist in %s" % (self.recipe, self.context)) 

        # An image can be pulled instead
        elif "image" in params:

            # If going to pull an image, the context is a folder of same name
            self.context = self.name

            # Image is validated when it needs to be used / pulled
            self.image = params['image']

        # We are required to have build OR image
        else:
            bot.exit("build or image must be defined for %s" % self.name)


# Volumes and Ports

    def set_volumes(self, params):
        '''set volumes from the recipe
        '''
        self.volumes = params.get('volumes', [])
        self._volumes_from = params.get('volumes_from', [])
        
    def set_volumes_from(self, instances):
        '''volumes from is called after all instances are read in, and
           then volumes can be mapped (and shared) with both containers.
           with Docker, this is done with isolation, but for Singularity
           we will try sharing a bind on the host.

           Parameters
           ==========
           instances: a list of other instances to get volumes from
        '''
        for name in self._volumes_from:
            if name not in instances:
                bot.exit('%s not in config is specified to get volumes from.' % name)
            for volume in instances[name].volumes:
                if volume not in self.volumes:
                    self.volumes.append(volume)

    def get_ports(self, params):
        '''set ports from the recipe to be used
        '''
        self.ports = params.get('ports', [])
