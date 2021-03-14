"""

Copyright (C) 2019-2021 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

import errno
import json
import os
import pwd
import sys
import yaml

from subprocess import Popen, PIPE, STDOUT


def get_installdir():
    """get_installdir returns the installation directory of the application"""
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def get_userhome():
    """get the user home based on the effective uid"""
    return pwd.getpwuid(os.getuid())[5]


def run_command(cmd, sudo=False):
    """run_command uses subprocess to send a command to the terminal.

    Parameters
    ==========
    cmd: the command to send, should be a list for subprocess
    error_message: the error message to give to user if fails,
    if none specified, will alert that command failed.

    """
    if sudo is True:
        cmd = ["sudo"] + cmd

    try:
        output = Popen(cmd, stderr=STDOUT, stdout=PIPE)

    except FileNotFoundError:
        cmd.pop(0)
        output = Popen(cmd, stderr=STDOUT, stdout=PIPE)

    t = output.communicate()[0], output.returncode
    output = {"message": t[0], "return_code": t[1]}

    if isinstance(output["message"], bytes):
        output["message"] = output["message"].decode("utf-8")

    return output


################################################################################
## FOLDER OPERATIONS ###########################################################
################################################################################


def mkdir_p(path):
    """mkdir_p attempts to get the same functionality as mkdir -p
    :param path: the path to create.
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            print("Error creating path %s, exiting." % path)
            sys.exit(1)


################################################################################
## FILE OPERATIONS #############################################################
################################################################################


def write_file(filename, content, mode="w"):
    """write_file will open a file, "filename" and write content, "content"
    and properly close the file
    """
    with open(filename, mode) as filey:
        filey.writelines(content)
    return filename


def read_file(filename, mode="r", readlines=True):
    """write_file will open a file, "filename" and write content, "content"
    and properly close the file
    """
    with open(filename, mode) as filey:
        if readlines is True:
            content = filey.readlines()
        else:
            content = filey.read()
    return content


# Yaml


def read_yaml(filename, mode="r", quiet=False):
    """read a yaml file, only including sections between dashes"""
    stream = read_file(filename, mode, readlines=False)
    return _read_yaml(stream, quiet=quiet)


def write_yaml(yaml_dict, filename, mode="w"):
    """write a dictionary to yaml file

    Parameters
    ==========
    yaml_dict: the dict to print to yaml
    filename: the output file to write to
    pretty_print: if True, will use nicer formatting
    """
    with open(filename, mode) as filey:
        filey.writelines(yaml.dump(yaml_dict))
    return filename


def _read_yaml(section, quiet=False):
    """read yaml from a string, either read from file (read_frontmatter) or
    from yml file proper (read_yaml)

    Parameters
    ==========
    section: a string of unparsed yaml content.
    """
    metadata = {}

    # PyYaml vs pyaml have subtle differences
    if hasattr(yaml, "FullLoader"):
        docs = yaml.load_all(section, Loader=yaml.FullLoader)
    else:
        docs = yaml.load_all(section)

    for doc in docs:
        if isinstance(doc, dict):
            for k, v in doc.items():
                if not quiet:
                    print("%s: %s" % (k, v))
                metadata[k] = v
    return metadata


# Json


def write_json(json_obj, filename, mode="w", print_pretty=True):
    """write_json will (optionally,pretty print) a json object to file

    Parameters
    ==========
    json_obj: the dict to print to json
    filename: the output file to write to
    pretty_print: if True, will use nicer formatting
    """
    with open(filename, mode) as filey:
        if print_pretty:
            filey.writelines(print_json(json_obj))
        else:
            filey.writelines(json.dumps(json_obj))
    return filename


def print_json(json_obj):
    """just dump the json in a "pretty print" format"""
    return json.dumps(json_obj, indent=4, separators=(",", ": "))


def read_json(filename, mode="r"):
    """read_json reads in a json file and returns
    the data structure as dict.
    """
    with open(filename, mode) as filey:
        data = json.load(filey)
    return data
