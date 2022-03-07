"""

Copyright (C) 2021-2022 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

import os
import sys

from jsonschema.exceptions import ValidationError

from scompose.utils import read_yaml

# We don't require jsonschema, so catch import error and alert user
try:
    from jsonschema import validate
except ImportError as e:
    msg = "pip install jsonschema"
    sys.exit("jsonschema is required for checking and validation: %s\n %s" % (e, msg))


def validate_config(filepath):
    """
    Validate a singularity-compose.yaml file.
    """
    try:
        cfg = read_yaml(filepath, quiet=True)
        validate(cfg, compose_schema)
        return True
    except ValidationError:
        return False


## Singularity Compose Schema

schema_url = "https://json-schema.org/draft-07/schema/#"

# Common patterns of types
string_list = {"type": "array", "items": {"type": "string"}}

# Instance groups
instance_build = {
    "type": "object",
    "properties": {
        "recipe": {"type": "string"},
        "context": {"type": "string"},
        "options": string_list,
    },
}

instance_network = {
    "type": "object",
    "properties": {
        "allocate_ip": {"type": "boolean"},
        "enable": {"type": "boolean"},
    },
}


instance_start = {
    "type": "object",
    "properties": {
        "args": {"type": ["string", "array"]},
        "options": string_list,
    },
}

instance_run = {
    "type": "object",
    "properties": {
        "args": {"type": ["string", "array"]},
        "options": string_list,
    },
}

instance_post = {
    "type": "object",
    "properties": {
        "commands": string_list,
    },
}

instance_exec = {
    "type": "object",
    "properties": {"options": string_list, "command": {"type": "string"}},
    "required": [
        "command",
    ],
}

instance_deploy = {
    "type": "object",
    "properties": {
        "replicas": {"type": "number", "minimum": 1},
    },
}

# A single instance
instance = {
    "type": "object",
    "properties": {
        "image": {"type": "string"},
        "build": instance_build,
        "network": instance_network,
        "ports": string_list,
        "volumes": string_list,
        "volumes_from": string_list,
        "depends_on": string_list,
        "start": instance_start,
        "exec": instance_exec,
        "run": {"oneOf": [instance_run, {"type": "array"}]},
        "post": instance_post,
        "deploy": instance_deploy,
    },
}


# instances define container services
instances = {"type": "object", "patternProperties": {"\\w[\\w-]*": instance}}

properties = {"version": {"type": "string"}, "instances": instances}

compose_schema = {
    "$schema": schema_url,
    "title": "Singularity Compose Schema",
    "type": "object",
    "required": [
        "version",
        "instances",
    ],
    "properties": properties,
    "additionalProperties": False,
}
