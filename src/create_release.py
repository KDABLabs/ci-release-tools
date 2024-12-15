#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Creates a GitHub release
# example usage
# ./src/create_release.py --repo KDAlgorithms --version 1.4 --sha1 1fcdd65fb2dc46b67f238e6fee33ae7973421016

import sys
import argparse
import gh_utils
import changelog_utils

parser = argparse.ArgumentParser()

parser.add_argument("--repo", help="GitHub repository name", required=True)
parser.add_argument("--version", help="Release version", required=True)
parser.add_argument("--sha1", help="Sha1 for tagging", required=True)

args = parser.parse_args()

release_notes = changelog_utils.get_changelog(
    args.repo, args.version, args.sha1)

if not release_notes:
    print(f"No release found for version {args.version} in {args.sha1}")
    sys.exit(1)

gh_utils.create_release(args.repo, args.version, release_notes)
