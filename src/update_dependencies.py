#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT
#

# Prints and updates dependency versions for submodules
# Example, called by github to print:
# Print dependencies:
# ./src/update_dependencies.py --print-dependency-versions --proj-name KDStateMachineEditor --repo-path ../KDStateMachineEditor

import argparse
import gh_utils


def print_dependencies(proj_name, repo_path):
    '''
    Print dependencies for a project

    Args:
        proj_name: The name of the project (e.g. 'knut'). Must be a project in releasing.toml
        repo_path: Path to repository containing the project
    '''

    versions = gh_utils.get_submodule_versions(repo_path, proj_name)

    if versions:
        print("::group::Versions")

    # Print with annotation tags so it appears under GH actions results
    for version in versions:
        latest_version = version['latest_version']
        current_version = version['current_version']
        submodule_path = version['submodule_path']

        if latest_version == current_version or current_version == 'latest':
            print(
                f"::notice::{submodule_path} is up to date ({latest_version})")
        elif latest_version:
            print(
                f"::warning::{submodule_path} {current_version} can be bumped to {latest_version}")
        else:
            print(f"::error::Can't determine version of {submodule_path}")

    if versions:
        print("::endgroup::")


parser = argparse.ArgumentParser()
parser.add_argument('--print-dependency-versions', action='store_true',
                    help="prints dependency versions", required=False)

parser.add_argument('--proj-name', metavar='<path>',
                    help="Project like 'Knut'", required=True)

parser.add_argument('--repo-path', metavar='<path>',
                    help="Path to repository", required=True)

args = parser.parse_args()

if args.print_dependency_versions:
    print_dependencies(args.proj_name, args.repo_path)
