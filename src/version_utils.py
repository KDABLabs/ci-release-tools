#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

import re
from utils import download_file_as_string, get_project


def previous_version(version):
    '''
    Returns the previous version, example:
    2.1.1 -> 2.1.0
    2.1.0 -> 2.0.0
    2.0.0 -> 1.0.0

    Just to make sure we're not skipping versions when bumping.
    '''

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


def get_version_in_versiontxt(project_name, sha1):
    '''
    KD* projects compatible with release-plz have a version.txt which is read by CMakeLists.txt
    All projects are encouraged to port to this way as it's easier for tooling.
    '''
    filename = f"https://raw.githubusercontent.com/KDAB/{project_name}/{sha1}/version.txt"
    file_contents = download_file_as_string(filename)
    return file_contents.strip()


def get_current_version_in_cmake(proj_name, sha1):
    proj = get_project(proj_name)
    if not proj.get('has_version_txt', False):
        raise Exception(
            f"{proj_name} is missing a version.txt which should be read by CMake. Copy from Knut or KDDockWidgets please.")

    return get_version_in_versiontxt(proj_name, sha1)


def is_numeric(version):
    try:
        ver_split = version.split('.')
        int(ver_split[0])
        int(ver_split[1])
        int(ver_split[2])
        return True
    except:
        return False
