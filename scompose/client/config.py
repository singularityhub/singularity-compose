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

from scompose.project import Project
import logging
import json
import sys
import os


log = logging.getLogger(__name__)

def main(args, parser, extra):
    '''View or validate a configuration file

       This comes down to reading in the config to the project, at which
       case it is validated. We then print it for the user.
    '''
    working_dir = args.context
    if working_dir == ".":
        working_dir = os.getcwd()

    # Initialize the project
    project = Project(filename=args.file,
                      name=args.project_name,
                      working_dir=working_dir,
                      env_file=args.env_file)

    # Builds any containers into folders
    project.view_config()
