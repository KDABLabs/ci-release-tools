#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Scripts related to GitHub

# Examples:
# $ gh_utils.py --get-latest-release=KDAB/KDDockWidgets
# v2.1.0

import json
import argparse
from utils import get_projects, repo_exists, run_command, run_command_with_output, run_command_silent, tag_for_version, get_project, get_submodule_builtin_dependencies
from version_utils import is_numeric, previous_version, get_current_version_in_cmake
from changelog_utils import get_changelog


def get_latest_release_tag_in_github(repo, repo_path, main_branch, via_tag=False):
    """
    Returns the tag of latest release
    repo is for example 'KDAB/KDReports'. If None, then gh will be run inside the repo at cwd.
    If via_tag is true, we'll try git locally, instead of gh release, which doesn't require local repo.
    """

    if via_tag:
        cmd = f"git -C {repo_path} describe --tags --abbrev=0 {main_branch}"
        return run_command_with_output(cmd).strip()

    # Via gh release:
    try:
        repo_arg = f"--repo {repo}" if repo else ""

        cmd = f"gh release list {repo_arg} --limit 1"
        lines = run_command_with_output(cmd, repo_path).split('\n')
        if not lines or lines == ['']:
            return None

        # print(f"lines={lines}, cmd={cmd}, cwd={cwd}")

        # example:
        # TITLE            TYPE    TAG NAME         PUBLISHED
        # KDReports 2.3.0  Latest  kdreports-2.3.0  about 2 months ago
        version = lines[0].split('\t')
        if len(version) < 3:
            print(f"get_latest_release_tag_in_github: could not parse {lines}")
            return None
        version = version[2]
    except Exception as e:
        print(f"Failed to get latest release: {e}")
        return None
    return version


def tag_exists(repo, tag):
    return run_command_silent(f"gh api repos/KDAB/{repo}/git/refs/tags/{tag}")


def sha1_for_tag(repo_path, tag):
    """
    uses gh to create a tag
    """
    output = run_command_with_output(
        f"git -C {repo_path} rev-parse {tag}^{{commit}}")
    return output.strip()


def create_tag(proj_name, tag, sha1):
    cmd = f"gh api -X POST /repos/KDAB/{proj_name}/git/refs -f ref=refs/tags/{tag} -f sha={sha1}"
    return run_command(cmd)


def create_tag_via_git(proj_name, version, sha, repo_path):
    """
    uses git to create a sha
    """
    tag = tag_for_version(proj_name, version)
    if tag_exists(proj_name, tag):
        existing_tagged_sha1 = sha1_for_tag(repo_path, tag)
        if sha != existing_tagged_sha1:
            print(
                f"Tag {tag} already exists but points to different sha {sha} != {existing_tagged_sha1}!")
            return False
    else:
        cmd = f"git -C {repo_path} tag -a {tag} {sha} -m \"{proj_name} {tag}\""
        if not run_command(cmd):
            print(f"Failed to create tag {tag}")
            return False

    if not run_command(f"git -C {repo_path} push origin {tag}"):
        print(f"Failed to push tag {tag}")
        return False
    return True


def download_tarball(repo, tag, version):
    return run_command_silent(f"curl -L -o {repo.lower()}-{version}.tar.gz https://github.com/KDAB/{repo}/archive/refs/tags/{tag}.tar.gz")


def tarball_has_integrity(filename):
    return run_command_silent(f"tar tzf {filename}")


def sign_file(filename):
    return run_command(f"gpg --local-user \"KDAB Products\" --armor --detach-sign {filename}")


def can_bump_to(proj_name, version, sha1, check_ci=True):
    """
    Returns True if we can bump to the specified version
    Reasons not to, include:
        - The previous semantic tag doesn't exist
        - Version in CMake doesn't match
        - Changelog entry doesn't exist
        - CI has failures
    """
    if not is_numeric(version):
        print("Do not pass versions with prefixes")
        return False

    prev = previous_version(version)
    proj = get_project(proj_name)
    tag_prefix = proj['tag_prefix']

    new_tag = f"{tag_prefix}{version}"
    prev_tag = f"{tag_prefix}{prev}"
    if prev != '0.0.0' and not tag_exists(proj_name, prev_tag):
        print(f"Error: Can't tag {new_tag} without {prev_tag}")
        return False

    if not get_changelog(proj_name, version, sha1):
        print(f"Error: No changelog found for version {version}")
        return False

    cur_cmake_version = get_current_version_in_cmake(proj_name, sha1)
    if cur_cmake_version != version:
        print(
            f"You need to bump the version in CMakeLists.txt, currently it's at {cur_cmake_version}")
        return False

    if check_ci:
        ci_in_progress, ci_completed, ci_failed = ci_run_status(
            proj_name, sha1)
        if ci_in_progress:
            print("error: CI is still running, please try again later")
            return False

        if ci_failed:
            print(f"error: CI has failed jobs for sha1 {sha1}")
            return False

        if not ci_completed:
            print(f"error: CI doesn't have completed runs for {sha1}")
            return False

    return True


def release_exists(repo, tag):
    return run_command_silent(f"gh release view {tag} --repo KDAB/{repo}")


def create_release(repo, version, sha1, notes, repo_path, should_sign):
    tag = tag_for_version(repo, version)
    if not repo_exists(repo):
        print(f"error: unknown repo {repo}, check releasing.toml")
        return False

    if not can_bump_to(repo, version, sha1):
        print("error: Project not ready to be tagged.")
        return False

    if not create_tag_via_git(repo, version, sha1, repo_path):
        print("error: Could not create tag")
        return False

    if release_exists(repo, tag):
        print(f"error: release {tag} already exists in {repo}")
        return False

    if not download_tarball(repo, tag, version):
        print(f"error: failed to download tarball from repo {repo}")
        return False

    tarball = f"{repo}-{version}.tar.gz".lower()
    if not tarball_has_integrity(tarball):
        print(f"error: Tarball {tarball} is corrupted")
        return False

    files_to_upload = ""
    if should_sign:
        if not sign_file(tarball):
            print(f"error: Failed to sign {tarball}")
            return False
        files_to_upload = f"{tarball}.asc {tarball}"
    else:
        files_to_upload = f"{tarball}"

    cmd = f"gh release create {tag} " \
        f"--repo KDAB/{repo} " \
        f'--title "Release {tag}" ' \
        f'--notes "{notes}" ' + files_to_upload

    if not run_command(cmd):
        print("error: Could not create release")
        return False

    return True


def sign_and_upload(proj_name, version):
    """
    Since GH actions can't sign, here's a function that signs and uploads
    To be run locally, example:
        ./src/sign_and_upload.py --repo KDDockWidgets --version 2.2.1
    """
    tag = tag_for_version(proj_name, version)
    if not download_tarball(proj_name, tag, version):
        print(f"error: failed to download tarball for {proj_name}")
        return False

    tarball = f"{proj_name}-{version}.tar.gz".lower()
    if not sign_file(tarball):
        print(f"error: Failed to sign {tarball}")
        return False

    if not run_command(f"gh release upload -R KDAB/{proj_name} {tag} {tarball}.asc"):
        print("error: Could not create release")
        return False

    return True


def ci_run_status(proj_name, sha1):
    output = run_command_with_output(
        f"gh run list -R KDAB/{proj_name} --commit {sha1} --json status,name")

    try:
        output = json.loads(output)
    except Exception as e:
        print(f"Failed to parse JSON: {output}")
        raise e

    filtered_data = [
        item for item in output if item["name"] != "Create release"]

    in_progress = any(item["status"] ==
                      "in_progress" for item in filtered_data)
    completed = any(item["status"] == "completed" for item in filtered_data)

    failure_states = ["failure", "timed_out", "cancelled"]
    failed = any(item["status"] in failure_states for item in filtered_data)

    if in_progress or completed or failed:
        print(output)

    return in_progress, completed, failed


def get_submodule_dependency_version(repo_path):
    '''
    Runs git-describe on a sub-module, for example:
        git -C ../KDStateMachineEditor/3rdparty/graphviz describe --tags HEAD
        which returns: 11.0.0-546-gb4650ee85
    This won't update/init submodules, be sure to not run on an old checkout.
    '''
    return run_command_with_output(f"git -C {repo_path} describe --abbrev=0 --tags HEAD").strip()


def get_submodule_versions(master_repo_path, proj_name):
    '''
        returns the list of submodule current and latest versions for give project
        example:
            get_submodule_versions('../KDStateMachineEditor', 'KDStateMachineEditor')
            returns: [
                {
                    'name': 'graphviz',
                    'current_version': '11.0.0',
                    'latest_version': '12.2.1'
                }
            ]
    '''
    deps = get_submodule_builtin_dependencies(proj_name)
    if not deps.items():
        return []

    result = []
    for dep in deps.values():
        repo_path = master_repo_path + '/' + dep['submodule']
        submodule_main_branch = dep.get('main_branch', 'main')
        latest_version = get_latest_release_tag_in_github(
            None, repo_path, submodule_main_branch, True)
        current_version = get_submodule_dependency_version(repo_path)

        result.append({
            'submodule_name': dep['submodule'],
            'current_version': current_version,
            'latest_version': latest_version
        })
    return result


def print_submodule_versions(repo_paths):
    '''
    prints the versions of submodules used by all KD* projects
    This won't update/init submodules, be sure to not run on an old checkout.
    '''
    projs = get_projects()
    for proj in projs:
        versions = get_submodule_versions(repo_paths + '/' + proj, proj)
        for version in versions:
            latest_version = version['latest_version']
            current_version = version['current_version']
            submodule_name = version['submodule_name']

            if latest_version == current_version or current_version == 'latest':
                print(
                    f"    {submodule_name}: {current_version}")
            elif latest_version:
                print(
                    f"    {submodule_name}: {current_version} ({latest_version} is available)")
            else:
                print(
                    f"    {submodule_name}: {current_version} -> ????")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--get-latest-release', metavar='REPO',
                        help="returns latest release for a repo")
    args = parser.parse_args()
    if args.get_latest_release:
        print(get_latest_release_tag_in_github(
            args.get_latest_release, None, None))

# print_submodule_versions('..')
