#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Creates a GitHub release
# example usage
# ./src/create_release.py --repo KDAlgorithms --tag 1.4 --releasenotes 1.4_notes.txt

import gh_utils
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--repo", help="GitHub repository name", required=True)
parser.add_argument("--tag", help="Release tag", required=True)
parser.add_argument("--releasenotes", help="Path to release notes file", required=True)

args = parser.parse_args()

notes = ""
try:
    with open(args.releasenotes) as f:
        notes = f.read()
except IOError:
    print(f"Error: Could not read releasenotes file {args.releasenotes}")
    exit(1)

if not notes:
    print("No notes found in releasenotes file")
    exit(1)

gh_utils.create_release(args.repo, args.tag, notes)
