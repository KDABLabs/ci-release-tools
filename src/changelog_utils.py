#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

from utils import downloadFileAsString

def get_kddockwidgets_changelog(version, sha1):
    filename = f"https://raw.githubusercontent.com/KDAB/KDDockWidgets/{sha1}/Changelog"
    text = downloadFileAsString(filename)

    sections = text.split('* v')
    for section in sections:
        if section.startswith(version):
            return '* v' + section.strip()
    return ""

# Gets the changelog for the specified version
def get_changelog(proj_name, version, sha1):
    if proj_name == 'KDDockWidgets':
        return get_kddockwidgets_changelog(version, sha1)

    raise Exception(
        f"Don't know how to get changelog for project {proj_name}. IMPLEMENT ME")
