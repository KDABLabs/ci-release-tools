#!/usr/bin/env bash

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
    echo "  preset: asan, asan_ubsan, ubsan, tsan, profile, debug, or static"
    exit 1
fi

PRESET="$1"
QT_VERSION="$2"
PARENT_INSTALL_DIR="$3"
QTSRC_DIR="$4"

# KDAB repos have patches
KDAB_REPOS=("qtbase" "qtshadertools" "qtdeclarative" "qtwayland")
QT_REPOS=("qtsvg" "qt5compat" "qttools" "qtscxml" "qtremoteobjects")

ORDERED_REPOS=("qtbase" "qtsvg" "qtshadertools" "qtdeclarative" "qtwayland" "qt5compat" "qttools" "qtscxml" "qtremoteobjects")

INSTALL_DIR="$PARENT_INSTALL_DIR"/qt-"$QT_VERSION"-"$PRESET"

case "$PRESET" in
    asan|asan_ubsan|ubsan|tsan|msan|profile|debug|static)
        ;;
    *)
        echo "Error: Invalid preset '$PRESET'. Must be one of: asan, asan_ubsan, ubsan, tsan, msan, profile, debug, static"
        exit 1
        ;;
esac

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$PARENT_INSTALL_DIR"

build_qt_module() {
    local repo="$1"

    cd "$QTSRC_DIR/$repo"
    mkdir -p "build-${PRESET}" && cd "build-${PRESET}"
    "${INSTALL_DIR}/bin/qt-cmake" ..
    ninja -v && ninja install && cp compile_commands.json .. && cd ..
}

for repo in "${KDAB_REPOS[@]}"; do
    REPO_DIR="$QTSRC_DIR/$repo"
    if [ ! -d "$REPO_DIR" ]; then
        git clone "kdab:/KDAB/$repo.git" "$REPO_DIR"
        git -C $REPO_DIR remote add github "https://github.com/qt/$repo.git"
        git -C $REPO_DIR fetch github
    else
        echo "Updating KDAB repo '$repo'"
        git -C $REPO_DIR fetch origin
        git -C $REPO_DIR fetch github
        git -C $REPO_DIR clean -fdx
    fi
    if git -C $REPO_DIR rev-parse "origin/kdab/$QT_VERSION" -- >/dev/null 2>&1; then
        git -C $REPO_DIR checkout -B "kdab/$QT_VERSION" "origin/kdab/$QT_VERSION"
    else
        # It's also OK to checkout an arbitrary version we don't have patches for, specially when not doing UBSAN
        git -C $REPO_DIR checkout "$QT_VERSION"
    fi
done

for repo in "${QT_REPOS[@]}"; do
    REPO_DIR="$QTSRC_DIR/$repo"
    if [ ! -d "$REPO_DIR" ]; then
        git clone "https://github.com/qt/$repo.git" "$REPO_DIR"
    else
        echo "Updating Qt repo '$repo'"
        git -C $REPO_DIR fetch origin
        git -C $REPO_DIR clean -fdx
    fi
    if git -C $REPO_DIR rev-parse "origin/$QT_VERSION" -- >/dev/null 2>&1; then
        git -C $REPO_DIR checkout -B "$QT_VERSION" "origin/$QT_VERSION"
    else
        git -C $REPO_DIR checkout "$QT_VERSION"
    fi
done

git -C "$QTSRC_DIR/qttools" submodule update --init --recursive

echo "Building Qt $QT_VERSION with preset '$PRESET' in '$PARENT_INSTALL_DIR' from source at '$QTSRC_DIR'"

cd "$QTSRC_DIR"/
cp "$SCRIPT_DIR/CMakePresets.json" qtbase/
cd qtbase

BUILD_DIR="build-${PRESET}"
rm -rf "${INSTALL_DIR}"
rm -rf "${BUILD_DIR}"
cmake --preset="$PRESET" -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR"
cmake --build "$BUILD_DIR"/ --verbose
cmake --install "$BUILD_DIR"/
cp "${BUILD_DIR}"/compile_commands.json $QTSRC_DIR/qtbase/

for repo in "${ORDERED_REPOS[@]}"; do
    if [ "$repo" = "qtbase" ]; then
        continue
    fi

    build_qt_module "$repo"
done

strip -s "$INSTALL_DIR"/bin/* || true
