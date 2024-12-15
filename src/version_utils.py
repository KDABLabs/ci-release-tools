#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

from changelog_utils import get_changelog
from utils import downloadFileAsString, get_project
from gh_utils import tag_exists
import re

# example:
# 2.1.1 -> 2.1.0
# 2.1.0 -> 2.0.0
# 2.0.0 -> 1.0.0
# Just to make sure we're not skipping versions when bumping
def previous_version(version):
    ver_split = version.split('.')
    ver_major = int(ver_split[0])
    ver_minor = int(ver_split[1])
    ver_patch = int(ver_split[2])

    if ver_patch > 0:
        ver_patch -= 1
    elif ver_minor > 0:
        ver_minor -= 1
        ver_patch = 0
    elif ver_major > 0:
        ver_major -= 1
        ver_minor = 0
        ver_patch = 0
    else:
        raise Exception("Version cannot go lower than 0.0.0")

    return f"{ver_major}.{ver_minor}.{ver_patch}"

def get_kddockwidgets_version_in_cmake():
    filename = "https://raw.githubusercontent.com/KDAB/KDDockWidgets/refs/heads/main/CMakeLists.txt"
    cmake_contents = downloadFileAsString(filename)

    major_pattern = r'set\(KDDockWidgets_VERSION_MAJOR\s+(\d+)\)'
    minor_pattern = r'set\(KDDockWidgets_VERSION_MINOR\s+(\d+)\)'
    patch_pattern = r'set\(KDDockWidgets_VERSION_PATCH\s+(\d+)\)'

    major_match = re.search(major_pattern, cmake_contents)
    minor_match = re.search(minor_pattern, cmake_contents)
    patch_match = re.search(patch_pattern, cmake_contents)

    if not (major_match and minor_match and patch_match):
        return None

    major = major_match.group(1)
    minor = minor_match.group(1)
    patch = patch_match.group(1)

    return f"{major}.{minor}.{patch}"

def get_current_version_in_cmake(proj_name):
    # proj = get_project(proj_name)
    if proj_name == 'KDDockWidgets':
        return get_kddockwidgets_version_in_cmake()

    raise Exception(f"Don't know how to get version for project {proj_name}. IMPLEMENT ME")

def is_numeric(version):
    try:
        ver_split = version.split('.')
        int(ver_split[0])
        int(ver_split[1])
        int(ver_split[2])
        return True
    except:
        return False

# Returns True if we can bump to the specified version
# Reasons not to, include:
    # - The previous semantic tag doesn't exist
    # - Version in CMake doesn't match
    # - Changelog entry doesn't exist
def can_bump_to(proj_name, version):
    if not is_numeric(version):
        print("Do not pass versions with prefixes")
        return False

    prev = previous_version(version)
    proj = get_project(proj_name)
    tag_prefix = proj['tag_prefix']

    new_tag = f"{tag_prefix}{version}"
    prev_tag = f"{tag_prefix}{prev}"
    if prev != '0.0.0' and not tag_exists(proj_name, prev_tag):
        print(f"Error: Can't tag {new_tag} without {prev_tag}")
        return False

    if not get_changelog(proj_name, version):
        print(f"Error: No changelog found for version {version}")
        return False

    cur_cmake_version = get_current_version_in_cmake(proj_name)
    if cur_cmake_version != version:
        print(f"You need to bump the version in CMakeLists.txt, currently it's at {cur_cmake_version}")
        return False

    return True
