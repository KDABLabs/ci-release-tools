#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Scripts related to GitHub

# Examples:
# $ gh_utils.py --get-latest-release=KDAB/KDDockWidgets
# v2.1.0

import json
import argparse
from utils import repo_exists, run_command, run_command_with_output, run_command_silent, tag_for_version, get_project
from version_utils import is_numeric, previous_version, get_current_version_in_cmake
from changelog_utils import get_changelog

# Returns the tag of latest release
# repo is for example 'KDAB/KDReports'


def get_latest_release_tag_in_github(repo):
    lines = run_command_with_output(
        f"gh release list --repo {repo} --limit 1").split('\n')
    # example:
    # TITLE            TYPE    TAG NAME         PUBLISHED
    # KDReports 2.3.0  Latest  kdreports-2.3.0  about 2 months ago
    version = lines[0].split('\t')[2]
    return version


def tag_exists(repo, tag):
    return run_command_silent(f"gh api repos/KDAB/{repo}/git/refs/tags/{tag}")

# uses gh to create a tag


def create_tag(proj_name, tag, sha1):
    cmd = f"gh api -X POST /repos/KDAB/{proj_name}/git/refs -f ref=refs/tags/{tag} -f sha={sha1}"
    return run_command(cmd)

# uses git to create a sha


def create_tag_via_git(proj_name, version, sha, repo_path):
    tag = tag_for_version(proj_name, version)
    if tag_exists(proj_name, tag):
        print(f"Tag {tag} already exists!")
        return False

    cmd = f"git -C {repo_path} tag -a {tag} {sha} -m \"{proj_name} {tag}\""
    if not run_command(cmd):
        print(f"Failed to create tag {tag}")
        return False

    if not run_command(f"git -C {repo_path} push origin {tag}"):
        print(f"Failed to push tag {tag}")
        return False
    return True


def download_tarball(repo, tag):
    return run_command_silent(f"curl -L -o {repo}-{tag}.tar.gz https://github.com/KDAB/{repo}/archive/refs/tags/{tag}.tar.gz")


def tarball_has_integrity(filename):
    return run_command_silent(f"tar tzf {filename}")


def sign_file(filename):
    return run_command(f"gpg --local-user \"KDAB Products\" --armor --detach-sign {filename}")

# Returns True if we can bump to the specified version
# Reasons not to, include:
    # - The previous semantic tag doesn't exist
    # - Version in CMake doesn't match
    # - Changelog entry doesn't exist
    # - CI has failures


def can_bump_to(proj_name, version, sha1, check_ci=True):
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

    ci_in_progress, ci_completed, ci_failed = ci_run_status(proj_name, sha1)
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


def create_release(repo, version, sha1, notes, repo_path, should_sign, should_create_tag=True):
    tag = tag_for_version(repo, version)
    if not repo_exists(repo):
        print(f"error: unknown repo {repo}, check releasing.toml")
        return False

    if should_create_tag:
        if not can_bump_to(repo, version, sha1):
            print("error: Project not ready to be tagged.")
            return False

        if not create_tag_via_git(repo, version, sha1, repo_path):
            print("error: Could not create tag")
            return False
    else:
        if not tag_exists(repo, tag):
            print(f"error: tag {tag} doesn't exist in repo {repo}")
            return False

    if release_exists(repo, tag):
        print(f"error: release {tag} already exists in {repo}")
        return False

    if not download_tarball(repo, tag):
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


# Since GH actions can't sign, here's a function that signs and uploads
# To be run locally
def sign_and_upload(proj_name, version):
    tag = tag_for_version(proj_name, version)
    if not download_tarball(proj_name, tag):
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
    print("run: " + f"gh run list --commit {sha1} --json status,name")
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--get-latest-release', metavar='REPO',
                        help="returns latest release for a repo")
    args = parser.parse_args()
    if args.get_latest_release:
        print(get_latest_release_tag_in_github(args.get_latest_release))
