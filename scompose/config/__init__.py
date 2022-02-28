"""

Copyright (C) 2019-2022 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

import os

from scompose.logger import bot
from scompose.utils import read_yaml


def merge_config(file_list):
    """
    Given one or more config files, merge into one
    """
    yaml_files = []
    for f in file_list:
        try:
            # ensure file exists
            if not os.path.exists(f):
                bot.exit("%s does not exist." % f)

            # read yaml file
            yaml_files.append(read_yaml(f, quiet=True))
        except:  # ParserError
            bot.exit("Cannot parse %s, invalid yaml." % f)

    # merge/override yaml properties where applicable
    return _deep_merge(yaml_files)


def _deep_merge(yaml_files):
    """
    Merge yaml files into a single dict
    """
    base_yaml = None
    for idx, item in enumerate(yaml_files):
        if idx == 0:
            base_yaml = item
        else:
            base_yaml = _merge(base_yaml, item)

    return base_yaml


def _merge(a, b):
    """
    Merge dict b into a
    """
    for key in b:
        if key in a:
            # merge dicts recursively
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                a[key] = _merge(a[key], b[key])
            # if types are equal, b takes precedence
            elif isinstance(a[key], type(b[key])):
                a[key] = b[key]
            # if nothing matches then this means a conflict of types which shouldn't exist in the first place
            else:
                bot.exit("key '%s': type mismatch in different files." % key)
        else:
            a[key] = b[key]
    return a
