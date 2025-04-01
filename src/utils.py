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
        command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
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
        process = os.popen(command)
        output = process.read()
        exit_code = process.close()
        if exit_code:
            print(f"cmd failed: {command} cwd={cwd}")
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
        {'graphviz': {'submodule_path': '3rdparty/graphviz'} }
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
    return {k: v for k, v in deps.items() if 'submodule_path' in v}


def get_fetchcontent_builtin_dependencies(name):
    '''
    Like get_builtin_dependencies() but only honours fetchcontent, not submodules
    '''

    deps = get_builtin_dependencies(name)
    return {k: v for k, v in deps.items() if 'fetchcontent_path' in v}


def download_file_as_string(filename):
    '''
    Downloads a file and returns it as a string
    '''
    result = ""
    try:
        with urllib.request.urlopen(filename) as response:
            result = response.read().decode('utf-8')
    except Exception as e:
        exit_because(f"Failed to download {filename}: {e}")

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


def clone_repo(repo, callback):
    '''
    Clones repo into a temporary directory.
    Executes callback and deletes directory.
    '''
    with tempfile.TemporaryDirectory() as temp_dir:
        if run_command_silent(f"git clone {repo} {temp_dir}"):
            return callback(temp_dir)
        return False


def get_fetchcontents_from_code(cmake_code, dep_name=None):
    '''
    Parses code and returns 1 line per fetchcontents_declare
    '''
    fetchcontents = []
    lines = cmake_code.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('#') or line.strip().startswith('//'):
            continue

        if 'fetchcontent_declare' in line.lower():
            line = line.strip()
            if line.endswith('\\') or line.count('(') > line.count(')'):
                j = i + 1
                while j < len(lines):
                    if not lines[j].strip().startswith('#'):
                        line += ' ' + lines[j].strip()
                    if not lines[j].strip().endswith('\\') and line.count('(') == line.count(')'):
                        break
                    j += 1
            fetchcontents.append(line)

    # Each line is for example:
    # 'FetchContent_Declare( fmt GIT_REPOSITORY https://github.com/fmtlib/fmt.git GIT_TAG e69e5f977d458f2650bb346dadf2ad30c5320281)'
    result = []
    for line in fetchcontents:
        parts = [s.strip() for s in line.split()]

        try:
            name = parts[parts.index('GIT_REPOSITORY') - 1]
            if '(' in name:
                name = name.split('(')[1].strip(',')
            repo = parts[parts.index('GIT_REPOSITORY') +
                         1].strip(')').strip(',')
            sha1 = parts[parts.index('GIT_TAG') + 1].strip(')').strip()

            if dep_name and dep_name != name:
                continue

            result.append({
                'name': name,
                'repo': repo,
                'sha1': sha1
            })
        except (ValueError, IndexError):
            continue

    return result


def set_fetchcontent_sha1(filename, old_sha1, new_sha1, tag_name=None):
    '''
    Replaces GIT_TAG old sha1 with new sha1.
    It's a dumb replace, does not support if the sha1 appears more than once for whatever reason
    '''
    with open(filename, 'r', encoding='UTF-8') as f:
        content = f.read()

        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                continue

            if old_sha1 in line:
                # Remove any existing comment
                line = line.split('#')[0].rstrip()
                if tag_name:
                    lines[i] = line.replace(
                        old_sha1, f"{new_sha1} # {tag_name}")
                else:
                    lines[i] = line.replace(old_sha1, new_sha1)

        content = '\n'.join(lines)

        with open(filename, 'w', encoding='UTF-8') as f:
            f.write(content)

    return True
