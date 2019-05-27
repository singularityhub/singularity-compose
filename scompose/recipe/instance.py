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
        self.validate_params(params)
        self.name = set_name(name)

    def set_name(self, name):
        '''set the filename to read the recipe from. If not provided, defaults
           to singularity-compose.yml
        '''
        pwd = os.path.basename(os.path.dirname(os.path.abspath(self.filename)))
        self.name = (name or pwd).lower()
        

    def validate_params(self, params):
        '''validate parameters from the singularity-compose.yml.
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
