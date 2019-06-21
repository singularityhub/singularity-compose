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

__version__ = "0.0.13"
AUTHOR = 'Vanessa Sochat'
AUTHOR_EMAIL = 'vsochat@stanford.edu'
NAME = 'singularity-compose'
PACKAGE_URL = "http://www.github.com/singularityhub/singularity-compose"
KEYWORDS = 'singularity, compose'
DESCRIPTION = "simple orchestration for singularity containers"
LICENSE = "LICENSE"

################################################################################
# Global requirements


INSTALL_REQUIRES = (
    ('spython', {'min_version': '0.0.68'}),
    ('pyaml', {'min_version': '5.1.1'}),
)

TESTS_REQUIRES = (
    ('pytest', {'min_version': '4.6.2'}),
)

INSTALL_REQUIRES_ALL = INSTALL_REQUIRES
