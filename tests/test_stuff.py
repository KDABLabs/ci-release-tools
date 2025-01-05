#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

import os
import version_utils
import gh_utils


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


def test_submodule_versions():
    '''
    Tests gh_utils.get_submodule_versions()
    We have knut as a submodule, do not bump it
    '''
    script_dir = os.path.dirname(os.path.realpath(__file__))
    knut_dir = script_dir + '/submodules/knut/'

    versions = gh_utils.get_submodule_versions(knut_dir, 'Knut')
    assert len(versions) == 9
    assert versions == [{'submodule_path': '3rdparty/extra-cmake-modules', 'current_version': 'v5.110.0', 'latest_version': 'v6.9.0'}, {'submodule_path': '3rdparty/kdalgorithms', 'current_version': '1.2', 'latest_version': '1.4'}, {'submodule_path': '3rdparty/ksyntaxhighlighting', 'current_version': 'v5.110.0', 'latest_version': 'v6.9.0'}, {'submodule_path': '3rdparty/nlohmann-json', 'current_version': 'v3.11.2', 'latest_version': 'v3.11.3'}, {'submodule_path': '3rdparty/pugixml',
                                                                                                                                                                                                                                                                                                                                                                                                                                                                'current_version': 'latest', 'latest_version': 'latest'}, {'submodule_path': '3rdparty/spdlog', 'current_version': 'v1.14.1', 'latest_version': 'v0.17.0'}, {'submodule_path': '3rdparty/tree-sitter', 'current_version': 'v0.20.8', 'latest_version': 'v0.24.1'}, {'submodule_path': '3rdparty/tree-sitter-cpp', 'current_version': 'v0.20.2', 'latest_version': 'v0.23.4'}, {'submodule_path': '3rdparty/tree-sitter-qmljs', 'current_version': '0.1.2', 'latest_version': '0.2.0'}]
