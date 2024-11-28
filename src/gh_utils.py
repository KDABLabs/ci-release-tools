#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Scripts related to GitHub

# Examples:
# $ gh_utils.py --get-latest-release=KDAB/KDDockWidgets
# v2.1.0

import argparse
from .utils import run_command_with_output

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--get-latest-release', metavar='REPO',
                        help="returns latest release for a repo")
    args = parser.parse_args()
    if args.get_latest_release:
        print(get_latest_release_tag_in_github(args.get_latest_release))
