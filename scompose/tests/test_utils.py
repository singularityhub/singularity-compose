#!/usr/bin/python

# Copyright (C) 2017-2021 Vanessa Sochat.

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pytest

here = os.path.dirname(os.path.abspath(__file__))


def test_write_read_files(tmp_path):
    """test_write_read_files will test the functions write_file and read_file"""
    print("Testing utils.write_file...")
    from scompose.utils import write_file

    tmpfile = str(tmp_path / "written_file.txt")
    assert not os.path.exists(tmpfile)
    write_file(tmpfile, "hello!")
    assert os.path.exists(tmpfile)

    print("Testing utils.read_file...")
    from scompose.utils import read_file

    content = read_file(tmpfile)[0]
    assert content == "hello!"


def test_write_bad_json(tmp_path):
    from scompose.utils import write_json

    bad_json = {"Wakkawakkawakka'}": [{True}, "2", 3]}
    tmpfile = str(tmp_path / "json_file.txt")
    assert not os.path.exists(tmpfile)
    with pytest.raises(TypeError):
        write_json(bad_json, tmpfile)


def test_write_json(tmp_path):
    import json
    from scompose.utils import write_json, read_json

    good_json = {"Wakkawakkawakka": [True, "2", 3]}
    tmpfile = str(tmp_path / "good_json_file.txt")
    assert not os.path.exists(tmpfile)
    write_json(good_json, tmpfile)
    with open(tmpfile, "r") as f:
        content = json.loads(f.read())
    assert isinstance(content, dict)
    assert "Wakkawakkawakka" in content
    content = read_json(tmpfile)
    assert "Wakkawakkawakka" in content


def test_get_installdir():
    """get install directory should return the base of where sregistry
    is installed
    """
    print("Testing utils.get_installdir")
    from scompose.utils import get_installdir

    whereami = get_installdir()
    print(whereami)
    assert whereami.endswith("scompose")


def test_run_command():
    print("Testing utils.run_command")
    from scompose.utils import run_command

    result = run_command(["echo", "hello"])
    assert result["message"] == "hello\n"
    assert result["return_code"] == 0


def test_get_userhome():
    print("Testing utils.get_userhome")
    from scompose.utils import get_userhome

    home = get_userhome()
    assert home in os.environ.get("HOME")


def test_print_json():
    print("Testing utils.print_json")
    from scompose.utils import print_json

    result = print_json({1: 1})
    assert result == '{\n    "1": 1\n}'


def test_merge():
    print("Testing utils._merge")
    from scompose.utils import _merge

    # No override
    a = {"a": 123}
    b = {"b": 456}
    assert _merge(a, b) == {"a": 123, "b": 456}

    # Override + merge
    a = {"a": 123}
    b = {"b": 456, "a": 789}
    assert _merge(a, b) == {"a": 789, "b": 456}

    # Override only
    a = {"a": 123}
    b = {"a": 789}
    assert _merge(a, b) == {"a": 789}

    # Dict merge
    a = {"a": 123, "b": {"c": "d"}}
    b = {"b": {"e": "f"}}
    assert _merge(a, b) == {"a": 123, "b": {"c": "d", "e": "f"}}

    # Dict merge + key override
    a = {"a": 123, "b": {"c": "d"}}
    b = {"b": {"c": "f"}}
    assert _merge(a, b) == {"a": 123, "b": {"c": "f"}}


def test_deep_merge():
    print("Testing utils._deep_merge")
    from scompose.utils import _deep_merge, read_yaml
    config_override = os.path.join(here, "configs", "config_override")

    # single file
    yaml_files = [
        read_yaml(
            os.path.join(config_override, "singularity-compose-1.yml"), quiet=True
        )
    ]
    ret = _deep_merge(yaml_files)
    assert ret["instances"] == {
        "echo": {
            "build": {"context": ".", "recipe": "Singularity"},
            "start": {"args": "arg0 arg1 arg2"},
        }
    }

    # multiple files
    yaml_files = [
        read_yaml(
            os.path.join(config_override, "singularity-compose-1.yml"), quiet=True
        ),
        read_yaml(
            os.path.join(config_override, "singularity-compose-2.yml"), quiet=True
        ),
    ]
    ret = _deep_merge(yaml_files)
    assert ret["instances"] == {
        "echo": {
            "build": {"context": ".", "recipe": "Singularity"},
            "start": {"args": "arg0 arg1", "options": ["fakeroot"]},
        },
        "hello": {
            "image": "from_the_other_side.sif",
            "start": {"args": "how are you?"},
        },
    }


def test_build_interpolated_config():
    print("Testing utils.build_interpolated_config")
    from scompose.utils import build_interpolated_config
    config_override = os.path.join(here, "configs", "config_override")

    # single file
    file_list = [os.path.join(config_override, "singularity-compose-1.yml")]
    ret = build_interpolated_config(file_list)
    assert ret["instances"] == {
        "echo": {
            "build": {"context": ".", "recipe": "Singularity"},
            "start": {"args": "arg0 arg1 arg2"},
        }
    }

    # multiple files
    file_list = [
            os.path.join(config_override, "singularity-compose-1.yml"),
            os.path.join(config_override, "singularity-compose-2.yml"),
    ]
    ret = build_interpolated_config(file_list)
    assert ret["instances"] == {
        "echo": {
            "build": {"context": ".", "recipe": "Singularity"},
            "start": {"args": "arg0 arg1", "options": ["fakeroot"]},
        },
        "hello": {
            "image": "from_the_other_side.sif",
            "start": {"args": "how are you?"},
        },
    }
