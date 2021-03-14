"""

Copyright (C) 2019-2021 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""

from scompose.project import Project


def main(args, parser, extra):
    """Build or rebuild containers

    Containers are built once and then named as <project>_<service>,
    e.g. `folder_db`. If a Singularity recipe changes for a container folder,
    you can run "singularity-compose build" to rebuild it.
    """
    # Initialize the project
    project = Project(
        filename=args.file, name=args.project_name, env_file=args.env_file
    )

    # Builds any containers into folders
    project.build(args.names)
