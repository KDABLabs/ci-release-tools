#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

from utils import downloadFileAsString, exit_because, get_project
import re

def get_kddockwidgets_changelog(version):

    filename = "https://raw.githubusercontent.com/KDAB/KDDockWidgets/refs/heads/main/Changelog"
    text = downloadFileAsString(filename)

    sections = text.split('* v')
    for section in sections:
        if section.startswith(version):
            return '* v' + section.strip()
    return ""

# Gets the changelog for the specified version
# The file needs to be in main/master branch
def get_changelog(proj_name, version):
    proj = get_project(proj_name)
    if proj_name == 'KDDockWidgets':
        return get_kddockwidgets_changelog(version)

    raise Exception(f"Don't know how to get changelog for project {proj_name}. IMPLEMENT ME")
