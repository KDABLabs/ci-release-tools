#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# example test:
# ./src/create_release.py --only-print-changelog --repo GammaRay --version 3.2.0 --sha1 master --repo-path ../GammaRay

from utils import download_file_as_string


def get_kddockwidgets_changelog(version, sha1):
    filename = f"https://raw.githubusercontent.com/KDAB/KDDockWidgets/{sha1}/Changelog"
    text = download_file_as_string(filename)

    sections = text.split('* v')
    for section in sections:
        if section.startswith(version):
            return '* v' + section.strip()
    return ""


# In lack of better name get_generic_changelog() gets changelog from Gammaray or KDSME
# If your project has a different changelog format, consider normalizing, or just create
# a new parser.
def get_generic_changelog(version, repo, sha1):
    filename = f"https://raw.githubusercontent.com/KDAB/{repo}/{sha1}/CHANGES"
    text = download_file_as_string(filename)

    sections = text.split('Version ')
    for section in sections:
        if section.startswith(version):
            return 'Version ' + section.strip()
    return ""


def get_changelog(proj_name, version, sha1):
    '''
    Gets the changelog for the specified version
    '''
    if proj_name == 'KDDockWidgets':
        return get_kddockwidgets_changelog(version, sha1)
    if proj_name == 'KDStateMachineEditor' or proj_name == 'GammaRay':
        return get_generic_changelog(version, proj_name, sha1)

    raise Exception(
        f"Don't know how to get changelog for project {proj_name}. IMPLEMENT ME")
