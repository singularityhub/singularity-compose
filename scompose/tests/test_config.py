#!/usr/bin/python

# Copyright (C) 2017-2022 Vanessa Sochat.

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

here = os.path.dirname(os.path.abspath(__file__))


def test_merge():
    print("Testing utils._merge")
    from scompose.config import _merge

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
    from scompose.utils import read_yaml
    from scompose.config import _deep_merge

    config_override = os.path.join(here, "configs", "config_merge")

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


def test_merge_config():
    print("Testing utils.build_interpolated_config")
    from scompose.config import merge_config

    config_override = os.path.join(here, "configs", "config_merge")

    # single file
    file_list = [os.path.join(config_override, "singularity-compose-1.yml")]
    ret = merge_config(file_list)
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
    ret = merge_config(file_list)
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
