#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# example test:
# ./src/create_release.py --only-print-changelog --repo GammaRay --version 3.2.0 --sha1 master --repo-path ../GammaRay
# ./src/changelog_utils.py KDSoap 2.2.0

import sys

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

# KDSoap and KDReports have their changelog in the docs folder, and use the version in the filename


def get_docs_versioned_changelog(repo, version, sha1):
    parts = version.split('.')
    while len(parts) > 2 and parts[-1] == '0':
        parts.pop()
    version_underscored = '_'.join(parts)
    filename = f"https://raw.githubusercontent.com/KDAB/{repo}/{sha1}/docs/CHANGES_{version_underscored}.txt"
    return download_file_as_string(filename).strip()


def get_changelog(proj_name, version, sha1):
    '''
    Gets the changelog for the specified version
    '''
    if proj_name == 'KDDockWidgets' or proj_name == 'KDSingleApplication':
        return get_kddockwidgets_changelog(proj_name, version, sha1)
    if proj_name == 'KDStateMachineEditor' or proj_name == 'GammaRay':
        return get_generic_changelog(version, proj_name, sha1)
    if proj_name in ('KDSoap', 'KDReports'):
        return get_docs_versioned_changelog(proj_name, version, sha1)

    raise Exception(
        f"Don't know how to get changelog for project {proj_name}. IMPLEMENT ME")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <project> <version> [sha1]")
        sys.exit(1)
    proj = sys.argv[1]
    ver = sys.argv[2]
    sha = sys.argv[3] if len(sys.argv) > 3 else 'master'
    print(get_changelog(proj, ver, sha))
