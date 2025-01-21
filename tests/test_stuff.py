#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

import os
import version_utils
import gh_utils
import utils


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
    expected = [{'submodule_name': 'extra_cmake_modules', 'submodule_path': '3rdparty/extra-cmake-modules', 'current_version': 'v5.110.0', 'latest_version': 'v6.10.0'}, {'submodule_name': 'kdalgorithms', 'submodule_path': '3rdparty/kdalgorithms', 'current_version': '1.2', 'latest_version': '1.4'}, {'submodule_name': 'ksyntaxhighlighting', 'submodule_path': '3rdparty/ksyntaxhighlighting', 'current_version': 'v5.110.0', 'latest_version': 'v6.9.0'}, {'submodule_name': 'nlohmann_json', 'submodule_path': '3rdparty/nlohmann-json', 'current_version': 'v3.11.2', 'latest_version': 'v3.11.3'}, {'submodule_name': 'pugixml',
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                'submodule_path': '3rdparty/pugixml', 'current_version': 'v1.14', 'latest_version': 'latest'}, {'submodule_name': 'spdlog', 'submodule_path': '3rdparty/spdlog', 'current_version': 'v1.14.1', 'latest_version': 'v1.15.0'}, {'submodule_name': 'tree_sitter', 'submodule_path': '3rdparty/tree-sitter', 'current_version': 'v0.20.8', 'latest_version': 'v0.24.1'}, {'submodule_name': 'tree_sitter_cpp', 'submodule_path': '3rdparty/tree-sitter-cpp', 'current_version': 'v0.20.2', 'latest_version': 'v0.23.4'}, {'submodule_name': 'tree_sitter_qmljs', 'submodule_path': '3rdparty/tree-sitter-qmljs', 'current_version': '0.1.2', 'latest_version': '0.2.0'}]

    i = 0
    for submodule in versions:
        # we can't compare latest_version, as that changes upstream
        assert submodule['current_version'] == expected[i]['current_version']
        i += 1


def test_fetchcontent_versions():
    '''
    Tests gh_utils.get_current_fetchcontent_sha1s()
    We have kdutils as a submodule, do not bump it
    '''

    deps = utils.get_fetchcontent_builtin_dependencies('KDUtils')
    print(deps)
    assert deps == {'KDBindings': {'fetchcontent_path': 'cmake/dependencies.cmake', 'main_branch': 'main'}, 'fmt': {'fetchcontent_path': 'cmake/dependencies.cmake', 'main_branch': 'master'}, 'spdlog': {'fetchcontent_path': 'cmake/dependencies.cmake', 'main_branch': 'v1.x'},
                    'whereami': {'fetchcontent_path': 'cmake/dependencies.cmake', 'main_branch': 'master'}, 'mio': {'fetchcontent_path': 'cmake/dependencies.cmake', 'main_branch': 'master'}, 'doctest': {'fetchcontent_path': 'tests/CMakeLists.txt', 'main_branch': 'master'}}

    script_dir = os.path.dirname(os.path.realpath(__file__))
    kdutils_dir = script_dir + '/submodules/kdutils/'

    versions = gh_utils.get_current_fetchcontent_sha1s(kdutils_dir, 'KDUtils')
    print(versions)

    assert versions == [{'name': 'KDBindings', 'repo': 'https://github.com/KDAB/KDBindings.git', 'sha1': 'efb54c58c3c2fce280d7089617935ec265fe4e2d', 'main_branch': 'main'}, {'name': 'fmt', 'repo': 'https://github.com/fmtlib/fmt.git', 'sha1': 'e69e5f977d458f2650bb346dadf2ad30c5320281', 'main_branch': 'master'}, {'name': 'spdlog', 'repo': 'https://github.com/gabime/spdlog.git', 'sha1': '27cb4c76708608465c413f6d0e6b8d99a4d84302',
                                                                                                                                                                                                                                                                                                                         'main_branch': 'v1.x'}, {'name': 'whereami', 'repo': 'https://github.com/gpakosz/whereami', 'sha1': 'e4b7ba1be0e9fd60728acbdd418bc7195cdd37e7', 'main_branch': 'master'}, {'name': 'mio', 'repo': 'https://github.com/mandreyel/mio.git', 'sha1': '8b6b7d878c89e81614d05edca7936de41ccdd2da', 'main_branch': 'master'}, {'name': 'doctest', 'repo': 'https://github.com/doctest/doctest.git', 'sha1': 'v2.4.9', 'main_branch': 'master'}]
    versions = gh_utils.get_fetchcontent_versions(kdutils_dir, 'KDUtils')
    print(versions)
    assert len(versions) == 6

    expected = [{'name': 'KDBindings', 'current_version': 'v1.1.0', 'latest_version': 'v1.1.0'}, {'name': 'fmt', 'current_version': '10.2.1', 'latest_version': '11.1.2'}, {'name': 'spdlog', 'current_version': 'v1.14.1', 'latest_version': 'v1.15.0'}, {
        'name': 'whereami', 'current_version': '', 'latest_version': None}, {'name': 'mio', 'current_version': '', 'latest_version': None}, {'name': 'doctest', 'current_version': 'v2.4.9', 'latest_version': 'v2.4.11'}]
    i = 0
    for version in versions:
        # we can't compare latest_version, as that changes upstream
        assert version['current_version'] == expected[i]['current_version']
        i += 1
