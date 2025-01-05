#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

from utils import download_file_as_string


def get_kddockwidgets_changelog(version, sha1):
    filename = f"https://raw.githubusercontent.com/KDAB/KDDockWidgets/{sha1}/Changelog"
    text = download_file_as_string(filename)

    sections = text.split('* v')
    for section in sections:
        if section.startswith(version):
            return '* v' + section.strip()
    return ""


def get_changelog(proj_name, version, sha1):
    '''
    Gets the changelog for the specified version
    '''
    if proj_name == 'KDDockWidgets':
        return get_kddockwidgets_changelog(version, sha1)

    raise Exception(
        f"Don't know how to get changelog for project {proj_name}. IMPLEMENT ME")
