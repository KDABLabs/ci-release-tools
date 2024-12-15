#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Generic utils used by the other scripts

import os
import sys
import tomllib
import subprocess


def exit_because(reason):
    print(reason)
    sys.exit(1)

# runs a command but doesn't print to stdout/stderr


def run_command_silent(command):
    result = subprocess.run(
        command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def run_command(command, fatal=True):
    if os.system(command) == 0:
        return True

    if fatal:
        exit_because(f"Failed to run command: {command}")

    return False


def run_command_with_output(command):
    output = os.popen(command).read()
    return output


def repo_exists(repo):
    return repo in get_projects()


def get_projects():
    script_path = os.path.dirname(__file__)
    with open(f'{script_path}/../releasing.toml', 'rb') as f:
        toml_content = tomllib.load(f)
        return toml_content['project']
    return None

# example: get_project('KDReports')


def get_project(name):
    projects = get_projects()
    if name not in projects:
        exit_because(f"Project {name} does not exist")
    return projects[name]


# Downloads a file and returns it as a string
def download_file_as_string(filename):
    import urllib.request
    result = ""
    try:
        with urllib.request.urlopen(filename) as response:
            result = response.read().decode('utf-8')
    except Exception as e:
        exit_because(f"Failed to download changelog: {e}")

    return result


def tag_for_version(proj_name, version):
    proj = get_project(proj_name)
    return f"{proj['tag_prefix']}{version}"
