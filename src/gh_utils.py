#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Scripts related to GitHub

# Examples:
# $ gh_utils.py --get-latest-release=KDAB/KDDockWidgets
# v2.1.0

import argparse
from utils import repo_exists, run_command, run_command_with_output, run_command_silent

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


def download_tarball(repo, tag):
    return run_command_silent(f"curl -L -o {repo}-{tag}.tar.gz https://github.com/KDAB/{repo}/archive/refs/tags/{tag}.tar.gz")


def tarball_has_integrity(filename):
    return run_command_silent(f"tar tzf {filename}")


def sign_file(filename):
    return run_command(f"gpg --local-user \"KDAB Products\" --armor --detach-sign {filename}")


def release_exists(repo, tag):
    return run_command_silent(f"gh release view {tag} --repo KDAB/{repo}")


def create_release(repo, tag, notes):
    if not repo_exists(repo):
        print(f"error: unknown repo {repo}, check releasing.toml")
        return False

    if not tag_exists(repo, tag):
        print(f"error: tag {tag} doesn't exist in repo {repo}")
        return False

    if release_exists(repo, tag):
        print(f"error: release {tag} already exists in {repo}")
        return False

    if not download_tarball(repo, tag):
        print(f"error: failed to download tarball from repo {repo}")
        return False

    tarball = f"{repo}-{tag}.tar.gz"
    if not tarball_has_integrity(tarball):
        print(f"error: Tarball {tarball} is corrupted")
        return False

    if not sign_file(tarball):
        print(f"error: Failed to sign {tarball}")
        return False

    cmd = f"gh release create {tag} " \
        f"--repo KDAB/{repo} " \
        f'--title "Release {tag}" ' \
        f'--notes "{notes}" ' \
        f"{tarball}.asc {tarball}"

    if not run_command(cmd):
        print("error: Could not create release")
        return False

    return True


def ci_run_status(proj_name, sha1):
    print("run: " + f"gh run list --commit {sha1} --json status,name")
    output = run_command_with_output(
        f"gh run list -R KDAB/{proj_name} --commit {sha1} --json status,name")
    in_progress = "in_progress" in output
    completed = "completed" in output
    failed = "failure" in output or "timed_out" in output or "cancelled" in output

    return in_progress, completed, failed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--get-latest-release', metavar='REPO',
                        help="returns latest release for a repo")
    args = parser.parse_args()
    if args.get_latest_release:
        print(get_latest_release_tag_in_github(args.get_latest_release))
