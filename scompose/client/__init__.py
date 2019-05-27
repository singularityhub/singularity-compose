#!/usr/bin/env python

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

import scompose
import argparse
import sys
import os


def get_parser():
    description = 'Orchestration for Singularity containers'
    parser = argparse.ArgumentParser(description="Singularity Compose")

    # Verbosity
    parser.add_argument('--verbose', dest="verbose", 
                        help="use verbose logging to debug.", 
                        default=False, action='store_true')

    parser.add_argument('--version', '-v', dest="version", 
                        help="print version and exit.", 
                        default=False, action='store_true')

    parser.add_argument("--log-level", default='INFO', 
                        dest='log_level', type=str,
                        help='logging level',
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

    # Global Variables
    parser.add_argument('--file', '-f' dest="file",
                        help="specify compose file (default singularity-compose.yml)", 
                        default="singularity-compose.yml")

    parser.add_argument("--project-name", '-p', default=None, 
                        dest='project_name', type=str,
                        help='specify project name (defaults to $PWD)')

    parser.add_argument("--project-directory", default=None, 
                        dest='project_dir', type=str,
                        help='specify project working directory (defaults to compose file location)')

    parser.add_argument("--env-file", default=None, 
                        dest='env_file', type=str,
                        help='an environment file to source')

    subparsers = parser.add_subparsers(help='scompose actions',
                                       title='actions',
                                       description=description,
                                       dest="command")

    # print version and exit
    version = subparsers.add_parser("version",
                                    help="show software version")

    build = subparsers.add_parser("build",
                                  help="Build or rebuild containers")

    config = subparsers.add_parser("config",
                                   help="Validate and view the compose file")

    create = subparsers.add_parser("create",
                                   help="create instances")

    down = subparsers.add_parser("down",
                                  help="stop instances")

    execute = subparsers.add_parser("exec",
                                    help="execute a command to a container")

    images = subparsers.add_parser("images",
                                    help="list images")

    kill = subparsers.add_parser("kill",
                                 help="kill instances")

    logs = subparsers.add_parser("logs",
                                 help="view output from instances")

    ps = subparsers.add_parser("ps",
                               help="list instances")

    restart = subparsers.add_parser("restart",
                                     help="restart images")

    rm = subparsers.add_parser("rm",
                               help="remove non-running container images")

    stop = subparsers.add_parser("stop",
                                 help="stop running containers")

    up = subparsers.add_parser("up",
                               help="build and start containers")

    # TODO: create simple singularity-compose file, read in
    # write recipes in folders
    # build recipes into containers in folders
    # then write commands

    return parser


def get_subparsers(parser):
    '''get_subparser will get a dictionary of subparsers, to help with printing help
    '''

    actions = [action for action in parser._actions 
               if isinstance(action, argparse._SubParsersAction)]

    subparsers = dict()
    for action in actions:
        # get all subparsers and print help
        for choice, subparser in action.choices.items():
            subparsers[choice] = subparser

    return subparsers


def setup_logging():
    logging.getLogger("requests").propagate = False
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)


def main():
    '''main is the entrypoint to singularity compose. We figure out the sub
       parser based on the command, and then import and call the appropriate 
       main.
    '''

    parser = get_parser()
    subparsers = get_subparsers(parser)

    def help(return_code=0):
        '''print help, including the software version and exit with return code
        '''
        version = scompose.__version__

        print("\nSingularity Compose v%s" % version)
        parser.print_help()
        sys.exit(return_code)
    
    # If the user didn't provide any arguments, show the full help
    if len(sys.argv) == 1:
        help()
    try:
        args = parser.parse_args()
    except:
        sys.exit(0)

    if args.debug is False:
        os.environ['MESSAGELEVEL'] = "DEBUG"

    # Show the version and exit
    if args.command == "version" or args.version == True:
        print(scompose.__version__)
        sys.exit(0)

    setup_logging()

    # Does the user want a shell?
    if args.command == "build": from .build import main
    elif args.command == "create": from .create import main
    elif args.command == "config": from .config import main
    elif args.command == "down": from .down import main
    elif args.command == "exec": from .exec import main
    elif args.command == "images": from .images import main
    elif args.command == "kill": from .kill import main
    elif args.command == "logs": from .logs import main
    elif args.command == "ps": from .ps import main
    elif args.command == "restart": from .restart import main
    elif args.command == "rm": from .rm import main
    elif args.command == "stop": from .stop import main
    elif args.command == "up": from .up import main
    
    # Pass on to the correct parser
    return_code = 0
    try:
        main(args=args,
             parser=parser,
             subparser=subparsers[args.command])
        sys.exit(return_code)
    except KeyboardInterrupt:
        log.error("Aborting.")
        return_code = 1
    except UnboundLocalError:
        return_code = 1

    sys.exit(return_code)

if __name__ == '__main__':
    main()
