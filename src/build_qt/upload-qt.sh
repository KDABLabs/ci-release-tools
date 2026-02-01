
#!/bin/bash

# SPDX-FileCopyrightText: 2026 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

set -e

# Uploads the specified Qt to GitHub so it can be used as CI
# These Qt's have asserts enabled and sanitizers, so they are not suitable for production use

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
    echo "Usage: $0 <qt-dir>"
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

# Get Qt version from qmake
QT_VERSION=$("$QMAKE_PATH" -query | grep QT_VERSION | cut -d: -f2)

if [ -z "$QT_VERSION" ]; then
    echo "Error: Could not determine Qt version"
    exit 1
fi

echo "Detected Qt version: $QT_VERSION"

# PACKAGE_NAME is something like qt-6.11-tsan
PACKAGE_NAME=$(basename "$QT_DIR")
TARBALL="${PACKAGE_NAME}.tar.zst"

echo "Creating tarball '$TARBALL' for Qt directory '$QT_DIR'..."
tar --zstd -cf "$TARBALL" -C "$QT_DIR" .

if gh release view "$QT_VERSION" --repo KDABLabs/ci-release-tools >/dev/null 2>&1; then
    echo "Release $QT_VERSION already exists; skipping creation."
else
    echo "Creating GitHub release for Qt '$QT_VERSION'..."
    gh release create "$QT_VERSION" --title "Developer $QT_VERSION for CI purposes" --notes "Do not use in production" --repo KDABLabs/ci-release-tools
fi

echo "Uploading tarball to GitHub Releases..."
gh release upload "$QT_VERSION" "$TARBALL" --repo KDABLabs/ci-release-tools

echo "Tarball created: $TARBALL at https://github.com/KDABLabs/ci-release-tools/releases/tag/$QT_VERSION"
cleanup
