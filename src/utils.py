#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Generic utils used by the other scripts

import os
import sys
import tomllib
import subprocess
import tempfile
import urllib.request


def exit_because(reason):
    print(reason)
    sys.exit(1)


def run_command_silent(command):
    '''
    runs a command but doesn't print to stdout/stderr
    '''
    result = subprocess.run(
        command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def run_command(command, fatal=True):
    if os.system(command) == 0:
        return True

    if fatal:
        exit_because(f"Failed to run command: {command}")

    return False


def run_command_with_output(command, cwd=None):
    current_dir = os.getcwd()
    if cwd:
        os.chdir(cwd)
    try:
        output = os.popen(command).read()
    finally:
        if cwd:
            os.chdir(current_dir)
    return output


def repo_exists(repo):
    return repo in get_projects()


def get_projects():
    script_path = os.path.dirname(__file__)
    with open(f'{script_path}/../releasing.toml', 'rb') as f:
        toml_content = tomllib.load(f)
        return toml_content['project']
    return None


def get_project(name):
    '''
    Reads releasing.toml and returns the specified project
    example: get_project('KDReports')
    '''
    projects = get_projects()
    if name not in projects:
        exit_because(f"Project {name} does not exist")
    return projects[name]


def get_builtin_dependencies(name):
    '''
    Returns the dependencies portion of releasing.toml
    For example, for 'KDStateMachineEditor it can return:
        {'graphviz': {'submodule': '3rdparty/graphviz'} }
    '''
    proj = get_project(name)
    try:
        return proj['dependencies']
    except KeyError:
        return {}


def get_submodule_builtin_dependencies(name):
    '''
    Like get_builtin_dependencies() but only honours submodules, not fetchcontent
    '''

    deps = get_builtin_dependencies(name)
    return {k: v for k, v in deps.items() if 'submodule' in v}


def download_file_as_string(filename):
    '''
    Downloads a file and returns it as a string
    '''
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


def create_tarball_with_submodules(proj_name, sha1, version):
    '''
    Create a release tarball including submodules.
    Some of our projects depend on unpopular submodules which aren't packaged anywhere.
    '''

    with tempfile.TemporaryDirectory() as temp_dir:
        clone_dir = f"{temp_dir}/{proj_name.lower()}-{version}"
        run_command(
            f"git clone https://github.com/KDAB/{proj_name} {clone_dir}")
        run_command(f"git -C {clone_dir} checkout {sha1}")
        run_command(f"git -C {clone_dir} submodule update --init --recursive")
        run_command(
            f"tar --exclude='.git' -C {temp_dir} -czvf {proj_name.lower()}-{version}.tar.gz {proj_name.lower()}-{version}")
