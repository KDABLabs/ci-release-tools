#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

from changelog_utils import get_changelog


def test_get_kdstatemachineeditor_changelog():
    """
    Test getting changelog for KDStateMachineEditor
    Using a known SHA and version to verify the changelog retrieval works correctly
    """
    # Using a known commit that has version 2.1.0 in the CHANGES file
    sha1 = "cfc67509d244feb9057a0941b7e7626d95cd2169"
    version = "2.1.0"

    changelog = get_changelog("KDStateMachineEditor", version, sha1)

    # Verify the changelog contains expected content
    assert changelog.startswith(f"Version {version}:")
    assert "KDStateMachineEditor now looks for Qt6 by default" in changelog

    # Test with non-existent version
    non_existent = get_changelog("KDStateMachineEditor", "9999.0.0", sha1)
    assert non_existent == ""

    # Print the changelog for debugging
    print(f"Changelog for KDStateMachineEditor {version}:")
    print(changelog)

    # Test invalid project name
    try:
        get_changelog("InvalidProject", version, sha1)
        assert False, "Should have raised an exception"
    except Exception as e:
        assert "Don't know how to get changelog for project" in str(e)
