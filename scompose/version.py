"""

Copyright (C) 2019-2022 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

__version__ = "0.1.18"
AUTHOR = "Vanessa Sochat"
AUTHOR_EMAIL = "vsoch@users.noreply.github.com"
NAME = "singularity-compose"
PACKAGE_URL = "http://github.com/singularityhub/singularity-compose"
KEYWORDS = "singularity, compose"
DESCRIPTION = "simple orchestration for singularity containers"
LICENSE = "LICENSE"

################################################################################
# Global requirements


INSTALL_REQUIRES = (
    ("spython", {"min_version": "0.2.11"}),
    ("pyaml", {"min_version": "5.1.1"}),
)

INSTALL_REQUIRES_CHECKS = INSTALL_REQUIRES + (("jsonschema", {"min_version": None}),)

TESTS_REQUIRES = (("pytest", {"min_version": "4.6.2"}),)

INSTALL_REQUIRES_ALL = INSTALL_REQUIRES
