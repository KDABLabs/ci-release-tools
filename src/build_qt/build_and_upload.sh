
#!/bin/bash

# SPDX-FileCopyrightText: 2026 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# example: ./build_and_upload.sh asan_ubsan v6.11.0-beta2 ~/installed/Qt/ ~/sources/qt6_ci

set -e

if [ $# -ne 4 ]; then
    echo "Usage: $0 <preset> <qt-version> <parent-install-dir> <qtsrc-dir>"
    echo "  preset: asan, asan_ubsan, ubsan, tsan, profile, or debug"
    exit 1
fi

PRESET="$1"
QT_VERSION="$2"
PARENT_INSTALL_DIR="$3"
QTSRC_DIR="$4"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$PARENT_INSTALL_DIR"/qt-"$QT_VERSION"-"$PRESET"

"$SCRIPT_DIR"/build.sh "$PRESET" "$QT_VERSION" "$PARENT_INSTALL_DIR" "$QTSRC_DIR"
"$SCRIPT_DIR"/upload-qt.sh "$INSTALL_DIR"
