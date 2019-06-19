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

from scompose.logger import bot
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
    parser.add_argument('--file', '-f', dest="file",
                        help="specify compose file (default singularity-compose.yml)", 
                        default="singularity-compose.yml")

    parser.add_argument("--project-name", '-p', default=None, 
                        dest='project_name', type=str,
                        help='specify project name (defaults to $PWD)')

    parser.add_argument("--project-directory", default=None, 
                        dest='working_dir', type=str,
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


    # Build

    build = subparsers.add_parser("build",
                                  help="Build or rebuild containers")


    # Config

    config = subparsers.add_parser("config",
                                   help="Validate and view the compose file")

    # Create (assumes built already), Up (will also build, if able)

    create = subparsers.add_parser("create",
                                   help="create instances")

    up = subparsers.add_parser("up",
                               help="build and start containers")

    for sub in [create, up]:
        sub.add_argument('--writable-tmpfs', dest="writable_tmpfs", 
                         help="allow the instance to write to tmp", 
                         default=False, action='store_true')

    # Down

    down = subparsers.add_parser("down",
                                  help="stop instances")

    execute = subparsers.add_parser("exec",
                                    help="execute a command to an instance")

    shell = subparsers.add_parser("shell",
                                   help="shell into an instance")


    kill = subparsers.add_parser("kill",
                                 help="kill instances")

    # Logs

    logs = subparsers.add_parser("logs",
                                 help="view output from instances")

    logs.add_argument("--tail", default=0, 
                      dest='tail', type=int,
                      help='clip logs to certain number of lines from end')

    logs.add_argument('--clear', dest="clear", 
                      help="clear existing logs.", 
                      default=False, action='store_true')

    ps = subparsers.add_parser("ps",
                               help="list instances")

    restart = subparsers.add_parser("restart",
                                     help="stop and start containers.")

    # Add list of names
    for sub in [create, down, logs, up]:
        sub.add_argument('names', nargs="*",
                          help='the names of the instances to target')

    # Only one name allowed
    for sub in [shell, execute, kill]:
        sub.add_argument('name', nargs=1,
                         help='the name of the instance to target')

    return parser


def main():
    '''main is the entrypoint to singularity compose. We figure out the sub
       parser based on the command, and then import and call the appropriate 
       main.
    '''
    parser = get_parser()

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
        args, extra = parser.parse_known_args()
    except:
        sys.exit(0)

    if args.verbose is False:
        os.environ['MESSAGELEVEL'] = "DEBUG"
    else:
        os.environ['MESSAGELEVEL'] = args.log_level

    # Show the version and exit
    if args.command == "version" or args.version is True:
        print(scompose.__version__)
        sys.exit(0)

    # Does the user want a shell?
    if args.command == "build": from .build import main
    elif args.command == "create": from .create import main
    elif args.command == "config": from .config import main
    elif args.command == "down": from .down import main
    elif args.command == "exec": from .exec import main
    elif args.command == "kill": from .kill import main
    elif args.command == "logs": from .logs import main
    elif args.command == "ps": from .ps import main
    elif args.command == "restart": from .restart import main
    elif args.command == "shell": from .shell import main
    elif args.command == "up": from .up import main
    
    # Pass on to the correct parser
    return_code = 0
    try:
        main(args=args, parser=parser, extra=extra)
        sys.exit(return_code)
    except KeyboardInterrupt:
        bot.exit("Aborting.")
    except UnboundLocalError:
        return_code = 1

    sys.exit(return_code)

if __name__ == '__main__':
    main()
