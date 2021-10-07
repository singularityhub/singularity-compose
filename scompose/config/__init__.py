import os
import sys

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
    cfg = read_yaml(filepath, quiet=True)
    return validate(cfg, compose_schema)


def merge_config(file_list):
    """
    Given one or more config files, merge into one
    """
    yaml_files = []
    for f in file_list:
        try:
            # ensure file exists
            if not os.path.exists(f):
                print("%s does not exist." % f)
                sys.exit(1)
            # read yaml file
            yaml_files.append(read_yaml(f, quiet=True))
        except:  # ParserError
            print("Cannot parse %s, invalid yaml." % f)
            sys.exit(1)

    # merge/override yaml properties where applicable
    return _deep_merge(yaml_files)


def _deep_merge(yaml_files):
    """
    Merge yaml files into a single dict
    """
    base_yaml = None
    for idx, item in enumerate(yaml_files):
        if idx == 0:
            base_yaml = item
        else:
            base_yaml = _merge(base_yaml, item)

    return base_yaml


def _merge(a, b):
    """
    Merge dict b into a
    """
    for key in b:
        if key in a:
            # merge dicts recursively
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                a[key] = _merge(a[key], b[key])
            # if types are equal, b takes precedence
            elif isinstance(a[key], type(b[key])):
                a[key] = b[key]
            # if nothing matches then this means a conflict of types which shouldn't exist in the first place
            else:
                print("key '%s': type mismatch in different files." % key)
                sys.exit(1)
        else:
            a[key] = b[key]
    return a
