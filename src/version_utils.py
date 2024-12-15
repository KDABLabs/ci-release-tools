#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

import re
from utils import download_file_as_string

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


def get_kddockwidgets_version_in_cmake(sha1):
    filename = f"https://raw.githubusercontent.com/KDAB/KDDockWidgets/{sha1}/CMakeLists.txt"
    cmake_contents = download_file_as_string(filename)

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


def get_current_version_in_cmake(proj_name, sha1):
    # proj = get_project(proj_name)
    if proj_name == 'KDDockWidgets':
        return get_kddockwidgets_version_in_cmake(sha1)

    raise Exception(
        f"Don't know how to get version for project {proj_name}. IMPLEMENT ME")


def is_numeric(version):
    try:
        ver_split = version.split('.')
        int(ver_split[0])
        int(ver_split[1])
        int(ver_split[2])
        return True
    except:
        return False
