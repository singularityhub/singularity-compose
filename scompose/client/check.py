"""

Copyright (C) 2021-2022 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

from scompose.logger import bot
from scompose.config import merge_config
from scompose.config.schema import validate_config
import yaml


def main(args, parser, extra):
    """
    Validate compose files for correctness.

    CLI Arguments
    ==========
        --preview flag to show combined configs.
    """

    # validate compose files
    for f in args.file:
        valid = validate_config(f)
        if valid and not args.preview:
            bot.info("%s is valid." % f)
        elif not valid:
            bot.exit("%s is not valid." % f)

    if args.preview:
        # preview
        config = merge_config(args.file)
        print(yaml.dump(config, sort_keys=False))
