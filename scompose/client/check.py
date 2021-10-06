"""

Copyright (C) 2021 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

from scompose.project.config import validate_config
from scompose.logger import bot


def main(args, parser, extra):
    """validate compose files for correctness.

    Eventually this will also have a --preview flag to show combined configs.
    """
    for f in args.file:
        result = validate_config(f)
        if not result:
            bot.info("%s is valid." % f)
        else:
            bot.exit("%s is not valid." % f)
