
#!/bin/bash

# SPDX-FileCopyrightText: 2026 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

set -e

# Ensure GitHub CLI is authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "Error: GitHub CLI is not authenticated. Run 'gh auth login'." >&2
    exit 1
fi

# Uploads the specified Qt to GitHub so it can be used as CI
# These Qt's have asserts enabled and sanitizers, so they are not suitable for production use

GH_RELEASE_NAME="qt-sanitizer-developer-builds"

cleanup() {
    if [ -f "$TARBALL" ]; then
        rm -f "$TARBALL"
    fi
}

error_handler() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Upload failed with exit code $exit_code"
        cleanup
    fi
}

trap error_handler EXIT

if [ $# -ne 1 ]; then
    echo "Usage: $0 <qt-installed-dir>"
    exit 1
fi

QT_DIR="$1"

if [ ! -d "$QT_DIR" ]; then
    echo "Error: Qt directory '$QT_DIR' does not exist."
    exit 1
fi

# Check if qmake exists
QMAKE_PATH="$QT_DIR/bin/qmake"
if [ ! -x "$QMAKE_PATH" ]; then
    echo "Error: qmake not found at '$QMAKE_PATH'"
    exit 1
fi

# Check if it works
QT_VERSION=$("$QMAKE_PATH" -query | grep QT_VERSION | cut -d: -f2)
if [ -z "$QT_VERSION" ]; then
    echo "Error: Could not determine Qt version"
    exit 1
fi

# PACKAGE_NAME is something like qt-6.11-tsan
PACKAGE_NAME=$(basename "$QT_DIR")
TARBALL="${PACKAGE_NAME}.tar.zst"

echo "Creating tarball '$TARBALL' for Qt directory "$PACKAGE_NAME" ..."
tar --zstd -cf "$TARBALL" -C "$QT_DIR" .

if gh release view "$GH_RELEASE_NAME" --repo KDABLabs/ci-release-tools >/dev/null 2>&1; then
    echo "Release $GH_RELEASE_NAME already exists; skipping creation."
else
    echo "Creating GitHub release '$GH_RELEASE_NAME'..."
    gh release create "$GH_RELEASE_NAME" --title "Developer Qt binaries for CI purposes" --notes "Do not use in production" --repo KDABLabs/ci-release-tools
fi

echo "Uploading tarball to GitHub Releases..."
gh release upload "$GH_RELEASE_NAME" "$TARBALL" --repo KDABLabs/ci-release-tools

echo "Tarball created: $TARBALL at https://github.com/KDABLabs/ci-release-tools/releases/tag/$GH_RELEASE_NAME"
cleanup
