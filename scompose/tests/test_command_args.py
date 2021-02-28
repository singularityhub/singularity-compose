#!/usr/bin/python

# Copyright (C) 2019-2021 Vanessa Sochat.

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

from scompose.logger import bot
from scompose.project import Project
from scompose.utils import run_command
from time import sleep
import shutil
import pytest
import os

here = os.path.dirname(os.path.abspath(__file__))


def test_command_args(tmp_path):
    bot.clear()  ## Clear previously logged messages

    cmd_args = os.path.join(here, "configs", "cmd_args")
    for filename in os.listdir(cmd_args):
        source = os.path.join(cmd_args, filename)
        dest = os.path.join(tmp_path, filename)
        print("Copying %s to %s" % (filename, dest))
        shutil.copyfile(source, dest)

    # Test the simple apache example
    os.chdir(tmp_path)

    # Check for required files
    assert "singularity-compose.yml" in os.listdir()

    print("Creating project...")

    # Loading project validates config
    project = Project()

    print("Testing build")
    project.build()

    assert "echo.sif" in os.listdir(tmp_path)

    print("Testing view config")
    project.view_config()

    print("Testing up")
    project.up()

    print("Waiting for instances to start")
    sleep(10)

    print("Bringing down")
    project.down()

    log = bot.get_logs()
    assert "echo arg0 arg1 arg2" in log
