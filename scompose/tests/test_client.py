#!/usr/bin/python

# Copyright (C) 2019-2022 Vanessa Sochat.

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

from scompose.project import Project
from scompose.utils import run_command
from time import sleep
import requests
import pytest
import os


def test_commands(tmp_path):

    tmpdir = os.path.join(tmp_path, "repo")
    repo = "https://github.com/singularityhub/singularity-compose-examples"

    # Clone the example
    run_command(["git", "clone", repo, tmpdir])

    # Test the simple apache example
    workdir = os.path.join(tmpdir, "v1.0", "apache-simple")
    os.chdir(workdir)

    # Check for required files
    assert "singularity-compose.yml" in os.listdir()

    print("Creating project...")

    # Loading project validates config
    project = Project()

    print("Testing build")
    assert "httpd.sif" not in os.listdir("httpd")
    project.build()
    assert "httpd.sif" in os.listdir("httpd")

    print("Testing view config")
    project.view_config()

    print("Testing up")
    project.up()
    assert "etc.hosts" in os.listdir()
    assert "resolv.conf" in os.listdir()

    print("Waiting for instance to start")
    sleep(10)

    print("Testing logs")
    project.logs(["httpd1"], tail=20)

    print("Clearing logs")
    project.clear_logs(["httpd1"])
    project.logs(["httpd1"], tail=20)

    print("Testing ps")
    project.ps()

    print("Testing exec")
    project.execute("httpd1", ["echo", "MarsBar"])

    # Ensure running
    print(requests.get("http://127.0.0.1").status_code)

    print("Testing down")
    project.down()

    print("Testing ip lookup")
    lookup = project.get_ip_lookup(["httpd1"])
    assert "httpd1" in lookup
    assert lookup["httpd1"] == "10.22.0.2"
