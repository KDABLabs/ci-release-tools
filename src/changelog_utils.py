#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# example test:
# ./src/create_release.py --only-print-changelog --repo GammaRay --version 3.2.0 --sha1 master --repo-path ../GammaRay

from utils import download_file_as_string

# Not KDDW specific anymore, KDSingleApplication uses the same format


def get_kddockwidgets_changelog(proj_name, version, sha1):
    filename = f"https://raw.githubusercontent.com/KDAB/{proj_name}/{sha1}/Changelog"
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

    # Remove lines starting with dashes
    text = '\n'.join([line for line in text.split(
        '\n') if not line.strip().startswith('-')])

    sections = text.split('Version ')
    for section in sections:
        if section.startswith(version):
            lines = section.strip().split('\n', 1)
            if len(lines) > 1:
                return lines[1].strip()
            return ""
    return ""


def get_changelog(proj_name, version, sha1):
    '''
    Gets the changelog for the specified version
    '''
    if proj_name == 'KDDockWidgets' or proj_name == 'KDSingleApplication':
        return get_kddockwidgets_changelog(proj_name, version, sha1)
    if proj_name == 'KDStateMachineEditor' or proj_name == 'GammaRay':
        return get_generic_changelog(version, proj_name, sha1)

    raise Exception(
        f"Don't know how to get changelog for project {proj_name}. IMPLEMENT ME")
