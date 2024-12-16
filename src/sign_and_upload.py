#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Allows to sign the source tarball after a release has been made
#
# Example:
#  python3 src/sign_and_upload.py --repo KDDockWidgets --version 2.2.0

# this will download source tarball for that tag, sign, and attach signature as asset

import argparse
import sys
from gh_utils import sign_and_upload

parser = argparse.ArgumentParser()

parser.add_argument("--repo", help="GitHub repository name", required=True)
parser.add_argument("--version", help="Release version", required=True)
args = parser.parse_args()

result = sign_and_upload(args.repo, args.version)

sys.exit(0 if result else -1)
