"""

Copyright (C) 2021 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

from scompose.project.config import validate_config
from scompose.logger import bot
from scompose.utils import build_interpolated_config, print_json


def main(args, parser, extra):
    """
    Validate compose files for correctness.

    CLI Arguments
    ==========
        --preview flag to show combined configs.
    """

    # validate compose files
    for f in args.file:
        result = validate_config(f)
        if not result:
            bot.info("%s is valid." % f)
        else:
            bot.exit("%s is not valid." % f)

    if args.preview:
        # preview
        config = build_interpolated_config(args.file)
        print("Combined configs:\n %s" % print_json(config))
