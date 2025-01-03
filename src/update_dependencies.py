#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT
#

# Prints and updates dependency versions for submodules
# Example, called by github to print:
# ./src/update_dependencies.py --print-dependency-versions KDStateMachineEditor --repo-path ../KDStateMachineEditor

import argparse
import gh_utils

parser = argparse.ArgumentParser()
parser.add_argument('--print-dependency-versions', dest='proj_name', metavar='<project name>',
                    help="prints dependency versions", required=True)
parser.add_argument('--repo-path', metavar='<path>',
                    help="Path to repository", required=True)

args = parser.parse_args()

versions = gh_utils.get_submodule_versions(args.repo_path, args.proj_name)


if versions:
    print("::group::Versions")

# Print with annotation tags so it appears under GH actions results
for version in versions:
    latest_version = version['latest_version']
    current_version = version['current_version']
    submodule_name = version['submodule_name']

    if latest_version == current_version or current_version == 'latest':
        print(f"::notice::{submodule_name} is up to date ({latest_version})")
    elif latest_version:
        print(
            f"::warning::{submodule_name} {current_version} can be bumped to {latest_version}")
    else:
        print(f"::error::Can't determine version of {submodule_name}")

if versions:
    print("::endgroup::")
