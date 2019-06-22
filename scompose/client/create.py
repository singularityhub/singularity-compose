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

def main(args, parser, extra):
    '''create one or more instances. If they don't exist, build first.

       This will build and bring up one or more named instances, or if None
       are provided, we create all of them.
    '''
    # Initialize the project
    project = Project(filename=args.file,
                      name=args.project_name,
                      env_file=args.env_file)

    # Create instances, and if none specified, create all
    project.create(args.names, 
                   writable_tmpfs=not args.read_only,
                   bridge=args.bridge,
                   no_resolv=args.no_resolv)
