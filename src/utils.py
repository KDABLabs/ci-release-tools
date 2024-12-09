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
    result = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
