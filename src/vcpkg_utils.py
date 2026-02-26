#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Scripts related to vcpkg

import requests
import json
import argparse
import sys


def fetch_vcpkg_port_vcpkg_json_file(port_name, vcpkg_repo="microsoft/vcpkg", vcpkg_branch="master"):
    """Fetches the vcpkg.json file for a port and returns its content."""
    url = f"https://raw.githubusercontent.com/{vcpkg_repo}/refs/heads/{vcpkg_branch}/ports/{port_name}/vcpkg.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching JSON: {e}")
        return None


def extract_version_from_vcpkg_json_file_content(vcpks_json_content):
    """Extracts the version from the vcpkg.json file content."""
    try:
        data = json.loads(vcpks_json_content)
        return data.get("version", None)
    except json.JSONDecodeError:
        print("Error parsing vcpkg.json file")
        return None


def get_latest_version_in_vcpkg(port_name, vcpkg_repo="microsoft/vcpkg", vcpkg_branch="master"):
    """Get the latest version for a vcpkg port."""
    json_data = fetch_vcpkg_port_vcpkg_json_file(port_name, vcpkg_repo, vcpkg_branch)
    if json_data:
        version = extract_version_from_vcpkg_json_file_content(json_data)
        return version


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--get-latest-vcpkg-version', type=str, metavar='PORT_NAME',
                        help="returns latest vcpkg version for a port")
    parser.add_argument('--vcpkg-repository', type=str, metavar='VCPKG_REPO', default="microsoft/vcpkg",
                        help="The vcpkg repository (optional, default: 'microsoft/vcpkg').")
    parser.add_argument('--vcpkg-branch', type=str, metavar='VCPKG_BRANCH', default="master",
                        help="The branch of the vcpkg repository (optional, default: 'master').")
    args = parser.parse_args()

    if args.get_latest_vcpkg_version:
        ret = get_latest_version_in_vcpkg(args.get_latest_vcpkg_version, args.vcpkg_repository, args.vcpkg_branch)
        if ret is None:
            sys.exit(1)
        print(ret)
        sys.exit(0)

    parser.print_help()
    sys.exit(1)
