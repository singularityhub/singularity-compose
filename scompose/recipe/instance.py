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
import os
import sys


class Instance(object):
    '''A section of a singularity-compose.yml, typically includes an image
       name, volumes, build directory, and any ports or environment variables
       relevant to the instance.
    '''
    def __init__(self, name, params={}):
        self.name = set_name(name, params)
        self.set_context(params)
        self.set_volumes(params)

    def set_name(self, name, params):
        '''set the instance name. First priority goes to name  parameter, then 
           to name in file
        '''
        self.name = params.get('name', name)
        
    def set_context(self, params):
        '''set and validate parameters from the singularity-compose.yml,
           including build (context and recipe)
        '''
        # build, build context, are required
        if "build" not in params:
            bot.exit("build section missing for %s" % self.name)

        if "context" not in params['build']:
            bot.exit("build.context section missing for %s" % self.name)

        self.context = params['build']['context']

        # The context folder must exist
        if not os.path.exists(self.context):
            bot.exit("build.context %s does not exist." % self.context)
 
        recipe = params['build'].get('recipe', 'Singularity')
        self.recipe = os.path.join(self.context, recipe)

        # The recipe must exist in the context folder
        if not os.path.exists(self.recipe):
            bot.exit("%s does not exist in %s" % (self.recipe, self.context)) 

# Volumes

    def set_volumes(self, params):
        '''set volumes from the recipe, including volumes. 
           TODO: after instances all read in, update each wrt. volumes_from
           WRITE ME VANESSA RAWR
        '''
'''
  nginx:
    build:
      context: ./nginx
      recipe: Singularity.nginx
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./uwsgi_params.par:/etc/nginx/uwsgi_params.par:ro
    volumes_from:
      - uwsgi
    ports:
      - "80"
'''
