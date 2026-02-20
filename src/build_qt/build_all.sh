#!/bin/bash

# SPDX-FileCopyrightText: 2026 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Builds Qt with all presets: asan, tsan, debug, and profile
# They all get installed to subdirectories of the given parent install dir.

if [ $# -ne 3 ]; then
    echo "Usage: $0 <qt-tag> <qt-src-dir> <qt-parent-install-dir>"
    exit 1
fi

QT_TAG=$1
QT_SRC_DIR=$2
QT_PARENT_INSTALL_DIR=$3

./build.sh asan "$QT_TAG" "$QT_PARENT_INSTALL_DIR" "$QT_SRC_DIR" && \
./build.sh ubsan "$QT_TAG" "$QT_PARENT_INSTALL_DIR" "$QT_SRC_DIR" && \
./build.sh tsan "$QT_TAG" "$QT_PARENT_INSTALL_DIR" "$QT_SRC_DIR" && \
./build.sh debug "$QT_TAG" "$QT_PARENT_INSTALL_DIR" "$QT_SRC_DIR" && \
./build.sh profile "$QT_TAG" "$QT_PARENT_INSTALL_DIR" "$QT_SRC_DIR"
