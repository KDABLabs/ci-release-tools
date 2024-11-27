#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Generic utils used by the other scripts

import os
import sys


def exit_because(reason):
    print(reason)
    sys.exit(1)


def run_command(command, fatal=True):
    if os.system(command) == 0:
        return True

    if fatal:
        exit_because(f"Failed to run command: {command}")

    return False


def run_command_with_output(command):
    output = os.popen(command).read()
    return output
