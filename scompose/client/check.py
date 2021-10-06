"""

Copyright (C) 2021 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

from scompose.project.config import validate_config
from scompose.logger import bot


def main(args, parser, extra):
    """validate a singularity-compose.yml for correctness.

    Eventually this will also have a --preview flag to show combined configs.
    """
    result = validate_config(args.file)
    if not result:
        bot.info("%s is valid." % args.file)
    else:
        bot.exit("%s is not valid." % args.file)
