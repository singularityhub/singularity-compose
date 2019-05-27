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

import logging
from six import binary_type

log = logging.getLogger(__name__)


class NoSuchService(Exception):
    def __init__(self, name):
        if isinstance(name, binary_type):
            name = name.decode('utf-8')
        self.name = name
        self.msg = "No such service: %s" % self.name

    def __str__(self):
        return self.msg

class ConnectionError(Exception):
    pass

