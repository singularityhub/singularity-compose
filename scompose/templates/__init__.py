"""

Copyright (C) 2019-2021 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

from scompose.logger import bot
from scompose.utils import get_installdir

import os


def get_template(name):
    """get a template by name from this directory. If does not exist,
    return None.
    """
    here = get_installdir()
    template = os.path.join(here, "templates", name)
    if os.path.exists(template):
        return template
    bot.warning("%s does not exist." % template)
