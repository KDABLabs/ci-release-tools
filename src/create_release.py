#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Creates a GitHub release
# example usage
# ./src/create_release.py --repo KDDockWidgets --version 2.2.1 --sha1 3aaccddc00a11a643e0959a24677838993de15ac --repo-path ../KDDockWidgets/ [--sign]

import sys
import os
import argparse
import gh_utils
import changelog_utils

parser = argparse.ArgumentParser()

parser.add_argument("--repo", help="GitHub repository name", required=True)
parser.add_argument("--version", help="Release version", required=True)
parser.add_argument("--sha1", help="Sha1 for tagging", required=True)
parser.add_argument("--sign", help="Sign the tag",
                    action="store_true", required=False)
parser.add_argument(
    "--repo-path", help="Path for repo being released", required=True)

args = parser.parse_args()

release_notes = changelog_utils.get_changelog(
    args.repo, args.version, args.sha1)

if not os.path.exists(args.repo_path):
    print(f"Error: Repository path {args.repo_path} does not exist")
    sys.exit(1)

if not release_notes:
    print(f"No release found for version {args.version} in {args.sha1}")
    sys.exit(1)

result = gh_utils.create_release(args.repo, args.version,
                                 args.sha1, release_notes, args.repo_path, args.sign)

sys.exit(0 if result else -1)
