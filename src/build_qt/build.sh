
#!/bin/bash

# SPDX-FileCopyrightText: 2026 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

set -e

error_handler() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Build failed with exit code $exit_code"
    fi
}

trap error_handler EXIT

if [ $# -ne 4 ]; then
    echo "Usage: $0 <preset> <qt-version> <parent-install-dir> <qtsrc-dir>"
    echo "  preset: asan, tsan, profile, or debug"
    exit 1
fi

PRESET="$1"
QT_VERSION="$2"
PARENT_INSTALL_DIR="$3"
QTSRC_DIR="$4"

case "$PRESET" in
    asan|tsan|profile|debug)
        ;;
    *)
        echo "Error: Invalid preset '$PRESET'. Must be one of: asan, tsan, profile, debug"
        exit 1
        ;;
esac

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$PARENT_INSTALL_DIR"

if [ ! -d "$QTSRC_DIR" ]; then
    git clone https://github.com/qt/qt5.git -b "$QT_VERSION" --depth 1 --single-branch "$QTSRC_DIR"
fi

cd "$QTSRC_DIR"/
git checkout "$QT_VERSION"

git submodule update --init --recursive -- . \
        ":(exclude)qtwebengine" \
        ":(exclude)qtpim" \
        ":(exclude)qttasktree" \
        ":(exclude)qtsystems" \
        ":(exclude)qtrepotools" \
        ":(exclude)qtquicktimeline" \
        ":(exclude)qtquickeffectmaker" \
        ":(exclude)qtquick3dphysics" \
        ":(exclude)qtquick3d" \
        ":(exclude)qtqa" \
        ":(exclude)qtopenapi" \
        ":(exclude)qtopcua" \
        ":(exclude)qtlottie" \
        ":(exclude)qthttpserver" \
        ":(exclude)qtgraphs" \
        ":(exclude)qtgamepad" \
        ":(exclude)qtfeedback" \
        ":(exclude)qtcoap" \
        ":(exclude)qtcanvas3d" \
        ":(exclude)qtactiveqt"

cp "$SCRIPT_DIR/CMakePresets.json" .

cd qtdeclarative/
git am < "$SCRIPT_DIR"/patches/qtdeclarative/0001-fix-build-with-UBSAN.patch || true
git am < "$SCRIPT_DIR"/patches/qtdeclarative/0002-Fix-more-UBSAN-linking.patch || true
cd ..

cd qtbase/
git am < "$SCRIPT_DIR"/patches/qtbase/0001-fix-ubsan.patch || true
cd ..

cd qtsvg/
git am < "$SCRIPT_DIR"/patches/qtsvg/0001-Fix-developer-build-with-UBSAN-enabled.patch || true
cd ..

cd qtshadertools/
git am < "$SCRIPT_DIR"/patches/qtshadertools/0001-Fix-UBSAN-build-due-to-invalid-down-cast.patch || true
git am < "$SCRIPT_DIR"/patches/qtshadertools/0002-Don-t-build-qsb-with-TSAN.patch || true
cd ..

INSTALL_DIR="$PARENT_INSTALL_DIR"/qt-"$QT_VERSION"-"$PRESET"
rm -rf "${INSTALL_DIR}"
cmake --preset="$PRESET" -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR"
cmake --build build-${PRESET}/
cmake --install build-${PRESET}/
