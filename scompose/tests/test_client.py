#!/usr/bin/python

# Copyright (C) 2019 Vanessa Sochat.

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

from scompose.project import Project
from scompose.utils import run_command
from time import sleep
import pytest
import tempfile
import shutil
import os


def test_commands(tmp_path):

    tmpdir = os.path.join(tmp_path, 'repo')
    repo = "https://github.com/singularityhub/singularity-compose-simple"

    # Clone the example
    run_command(["git", "clone", repo, tmpdir])
    os.chdir(tmpdir)

    # Check for required files
    assert 'singularity-compose.yml' in os.listdir()

    print('Creating project...')

    # Loading project validates config
    project = Project()

    print('Testing build')
    assert 'app.sif' not in os.listdir('app')
    project.build()
    assert 'app.sif' in os.listdir('app')

    print('Testing view config')
    project.view_config()

    print('Testing up')
    project.up()
    assert 'etc.hosts' in os.listdir()

    print('Waiting for instance to start')
    sleep(10)

    print('Testing logs')
    project.logs(['app'], tail=20)

    print('Clearing logs')
    project.clear_logs(['app'])
    project.logs(['app'], tail=20)

    print('Testing ps')
    project.ps()

    print('Testing exec')
    project.execute('app', ['echo','MarsBar'])

    # Ensure running
    assert requests.get('http://127.0.0.1/').status_code == 200

    assert 'db.sqlite3' in os.listdir('app')

    print('Testing down')
    project.down()

    print('Testing ip lookup')
    lookup = project.get_ip_lookup(['app'])
    assert 'app' in lookup
    assert lookup['app'] == '10.22.0.2'
    
    # Clean up
    shutil.rmtree(tmpdir)

if __name__ == '__main__':
    unittest.main()
