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


def test_circular_dependency(tmp_path):

    depends_on = os.path.join(here, "configs", "wrong_depends_on")
    for filename in os.listdir(depends_on):
        source = os.path.join(depends_on, filename)
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

    for image in ["first.sif", "second.sif", "third.sif"]:
        assert image in os.listdir(tmp_path)

    print("Testing view config")
    project.view_config()

    try:
        print("Testing up")
        project.up()
        raise Exception("Up should have failed")
    except SystemExit:
        print("Up failed as expected")
    finally:
        print("Bringing down")
        project.down()


def test_no_circular_dependency(tmp_path):
    bot.clear()  ## Clear previously logged messages

    depends_on = os.path.join(here, "configs", "depends_on")
    for filename in os.listdir(depends_on):
        source = os.path.join(depends_on, filename)
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

    for image in ["first.sif", "second.sif", "third.sif"]:
        assert image in os.listdir(tmp_path)

    print("Testing view config")
    project.view_config()

    # Test depends_on DAG order
    keys = list(project.instances.keys())
    assert keys == ["first", "second", "third"]

    print("Testing up")
    project.up()

    print("Waiting for instances to start")
    sleep(10)

    print("Bringing down")
    project.down()

    log = bot.get_logs()
    assert log.index("Creating first") < log.index("Creating second") and log.index(
        "Creating second"
    ) < log.index("Creating third")
