"""

Copyright (C) 2019-2021 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""

from scompose.project import Project


def main(args, parser, extra):
    """bring up one or more instances. They must exist.

    This will build and bring up one or more named instances, or if None
    are provided, we create all of them.
    """
    # Initialize the project
    project = Project(
        filename=args.file, name=args.project_name, env_file=args.env_file
    )

    # Create instances, and if none specified, create all
    project.down(args.names)

    # Create instances, and if none specified, create all
    project.up(
        args.names,
        writable_tmpfs=not args.read_only,
        bridge=args.bridge,
        no_resolv=args.no_resolv,
    )
