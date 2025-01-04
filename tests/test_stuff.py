#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

import version_utils


def test_get_version_in_versiontxt():
    '''
    tests version_utils.get_current_version_in_cmake() and
    indirectly version_utils.get_version_in_versiontxt()
    '''
    version = version_utils.get_current_version_in_cmake(
        'KDDockWidgets', 'main')
    assert version
    version_tokens = version.split('.')

    assert len(version_tokens) == 3
    assert version_utils.is_numeric(version)
