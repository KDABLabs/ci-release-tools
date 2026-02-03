
#!/bin/bash

# SPDX-FileCopyrightText: 2026 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Called by CI to download a sanitizer enabled Qt build, example:
# ./ci-download-qt.sh qt-v6.11.0-beta2-debug

set -e

error_handler() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Failed with exit code $exit_code"
    fi
}

trap error_handler EXIT

if [ $# -ne 1 ]; then
    echo "Usage: $0 <qt package name>"
    exit 1
fi

PACKAGE_NAME="$1"
TARBALL="${PACKAGE_NAME}.tar.zst"
DEST=~/Qt/${PACKAGE_NAME}

wget -O /tmp/${TARBALL} https://github.com/KDABLabs/ci-release-tools/releases/download/qt-sanitizer-developer-builds/${TARBALL}
rm -rf ${DEST}
mkdir -p ${DEST}

echo "Extracting Qt package /tmp/${TARBALL} to ${DEST} ..."
tar -xf /tmp/${TARBALL} -C ${DEST}

rm /tmp/${TARBALL}
