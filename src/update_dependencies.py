#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT
#

# Prints and updates dependency versions for submodules/fetchcontent
# Example, called by github to print:
# Print dependencies:
# ./src/update_dependencies.py --print-dependency-versions --proj-name KDStateMachineEditor --repo-path ../KDStateMachineEditor
# ./src/update_dependencies.py --update-dependency kdalgorithms --repo-path ../knut --proj-name Knut

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
    versions.extend(gh_utils.get_fetchcontent_versions(repo_path, proj_name))

    if versions:
        print("::group::Versions")

    # Print with annotation tags so it appears under GH actions results
    for version in versions:
        latest_version = version['latest_version']
        current_version = version['current_version']
        name = ''
        if 'submodule_path' in version:
            name = version['submodule_path']
        else:
            name = version['name']

        if (latest_version and latest_version == current_version) or current_version == 'latest':
            print(
                f"::notice::{name} is up to date ({latest_version})")
        elif latest_version:
            print(
                f"::warning::{name} {current_version} can be bumped to {latest_version}")
        else:
            print(f"::error::Can't determine version of {name}")

    if versions:
        print("::endgroup::")


parser = argparse.ArgumentParser()
parser.add_argument('--print-dependency-versions', action='store_true',
                    help="prints dependency versions", required=False)

parser.add_argument('--proj-name', metavar='<path>',
                    help="Project like 'Knut'", required=True)

parser.add_argument('--repo-path', metavar='<path>',
                    help="Path to repository", required=True)

parser.add_argument('--update-dependency', metavar='<dependency name>',
                    help="Dependency name", required=False, dest='dependency_name')

parser.add_argument('--remote', metavar='<remote>',
                    help="Remote, defaults to origin", required=False, default='origin')

parser.add_argument('--branch', metavar='<branch>',
                    help="Remote branch, defaults to the main branch", required=False)

parser.add_argument('--owner', metavar='<owner>',
                    help="Repo owner, usually KDAB", required=False, default='KDAB')

parser.add_argument('--sha1', metavar='<sha1, tag or branch>',
                    help="Sha tag or branch, defaults to latest", dest='new_sha1', required=False)

args = parser.parse_args()

if args.print_dependency_versions:
    print_dependencies(args.proj_name, args.repo_path)
elif args.dependency_name:
    gh_utils.update_dependency(args.proj_name, args.dependency_name,
                               args.new_sha1, args.repo_path,
                               args.remote, args.branch,
                               args.owner)
