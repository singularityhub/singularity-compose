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
from spython.main import get_client
import shlex as _shlex
import os
import sys


class Instance(object):
    '''A section of a singularity-compose.yml, typically includes an image
       name, volumes, build directory, and any ports or environment variables
       relevant to the instance.

       Parameters
       ==========
       name: should correspond to the section name for the instance.
       working_dir: should be the projects working directory, where a folder
                    named according to "name" is created for the image binary.
       params: all of the parameters defined in the configuration.
    '''
    def __init__(self, name, working_dir, sudo=False, params=None):

        if not params:
            params = {}

        self.image = None
        self.recipe = None
        self.instance = None
        self.sudo = sudo
        self.set_name(name, params)
        self.set_context(params)
        self.set_volumes(params)
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
        '''set the instance name. First priority goes to name  parameter, then 
           to name in file

           Parameters
           ==========
           name: the name of the instance, the first field in the config file.
           params: dictionary of key, value parameters
        '''
        self.name = params.get('name', name)
        

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
 
            self.recipe = params['build'].get('recipe', 'Singularity')

            # The recipe must exist in the context folder
            if not os.path.exists(os.path.join(self.context, self.recipe)):
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

    def set_ports(self, params):
        '''set ports from the recipe to be used
        '''
        self.ports = params.get('ports', [])

# Commands

    def _get_network_commands(self):
        '''take a list of ports, return the list of --network-args to
           ensure they are bound correctly.
        '''
        ports = []
        if self.ports:
            ports.append('--net')
            for pair in self.ports:
                ports += ['--network-args', '"portmap=%s/tcp"' % pair]
        return ports

    def _get_bind_commands(self):
        '''take a list of volumes, and return the bind commands for Singularity
        '''
        binds = []
        for volume in self.volumes:
            src, dest = volume.split(':') 

            # First try, assume file in root folder
            if not os.path.exists(os.path.abspath(src)):
                if os.path.exists(os.path.join(self.working_dir, src)):
                    src = os.path.join(self.working_dir, src)
                elif os.path.exists(os.path.join(self.working_dir, self.name, src)):
                    src = os.path.join(self.working_dir, self.name, src)
                else:
                    bot.exit('bind source file %s does not exist' % src)

            # For the src, ensure that it exists
            bind = "%s:%s" % (os.path.abspath(src), os.path.abspath(dest))
            binds += ['--bind', bind]
        return binds

# Image

    def get_image(self):
        '''get the associated instance image name, to be built if it doesn't
           exit. It can either be defined at the config from self.image, or 
           ultimately generated via a pull from a uri.
        '''
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
        return os.path.join(context, '%s.sif' % self.name)


# Build

    def build(self, working_dir):
        '''build an image if called for based on having a recipe and context.
           Otherwise, pull a container uri to the instance workspace.
        '''
        sif_binary = self.get_image()

        # If the final image already exists, don't continue
        if os.path.exists(sif_binary):
            return

        # Case 1: Given an image
        if self.image is not None:
            if not os.path.exists(self.image):
 
                # Can we pull it?
                if re.search('(docker|library|shub|http?s)[://]', self.image):
                    bot.info('Pulling %s' % self.image)
                    client.pull(self.image, name=sif_binary)

                else:
                    bot.exit('%s is an invalid unique resource identifier.' % self.image)

        # Case 2: Given a recipe
        elif self.recipe is not None:

            # Change directory to the context
            context = os.path.abspath(self.context)
            os.chdir(context)

            # The recipe is expected to exist in the context folder
            if not os.path.exists(self.recipe):
                bot.exit('%s not found for build' % self.recipe)
             
            # This will require sudo
            try:
                bot.info('Building %s' % self.name)
                self.client.build(name=sif_binary, recipe=self.recipe)
            except:
                build = "sudo singularity build %s %s" % (os.path.basename(sif_binary),
                                                          self.recipe)

                bot.warning("Please build with sudo: %s" % build)

            # Change back to provided working directory
            os.chdir(working_dir)

        else:
           bot.exit("neither image and build defined for %s" % self.name)

# State

    def exists(self):
        '''return boolean if an instance exists. We do this by way of listing
           instances, and so the calling user is important.
        '''
        instances = [x.name for x in self.client.instances(quiet=True, sudo=self.sudo)]
        return self.name in instances

    def get(self):
        '''If an instance exists, add to self.instance
        '''
        for instance in self.client.instances(quiet=True, sudo=self.sudo):
            if instance.name == self.name:
                self.instance = instance
                break

    def stop(self):
        '''delete the instance, if it exists. Singularity doesn't have delete
           or remove commands, everyting is a stop.
        '''
        if self.instance:
            bot.info("Stopping %s" % self)
            self.instance.stop(sudo=self.sudo)
            self.instance = None

# Create and Delete

    def up(self, working_dir, sudo=False, writable_tmpfs=False):
        '''up is the same as create, but like Docker, we build / pull instances
           first.
        '''
        image = self.get_image() or ''

        # Do a build if necessary
        if not os.path.exists(image):
            self.build(working_dir)
        self.create(writable_tmpfs=writable_tmpfs)


    def create(self, sudo=False, writable_tmpfs=False):
        '''create an instance, if it doesn't exist.
        '''
        image = self.get_image()

        # Case 1: No build context or image defined
        if image is None:
            bot.exit("Please define an image or build context for instance %s" % self.name)

        # Case 2: Image not built.
        if not os.path.exists(image):
            bot.exit("Image %s not found, please run build first." % image)

        # Finally, create the instance
        if not self.exists():

            bot.info("Creating %s" % self.name)

            # Volumes
            binds = self._get_bind_commands()

            # Ports
            ports = self._get_network_commands()

            # Hostname
            hostname = ["--hostname", self.name]

            # Writable Temporary Directory
            if writable_tmpfs:
                hostname += ['--writable_tmpfs']

            self.instance = self.client.instance(name=self.name,
                                                 sudo=self.sudo,
                                                 options=binds + ports + hostname,
                                                 image=image)
