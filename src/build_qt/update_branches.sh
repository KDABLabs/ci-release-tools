#!/bin/bash

# SPDX-FileCopyrightText: 2026 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

set -e

# Copies the KDAB patches from kdab/<from-branch> onto <to-branch> across the
# KDAB Qt repos, leaving the result on kdab/<to-branch>.
#
# <to-branch> is a Qt release tag or branch (e.g. v6.12.0-beta4, dev) living on
# the upstream qt/<repo> github mirror, not on the KDAB origin remote.
#
# The push is never run, only printed at the end, so the rebases can be
# inspected and built before anything reaches origin.
#
# A repo whose rebase conflicts is left mid-rebase for manual resolution and the
# remaining repos are still processed; conflicting repos are listed on exit.

if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    echo "Usage: $0 <from-branch> <to-branch> [qtsrc-dir]"
    echo "  e.g.: $0 v6.12.0-beta3 v6.12.0-beta4 ~/qt/src"
    echo "  copies kdab/v6.12.0-beta3 onto the v6.12.0-beta4 tag as kdab/v6.12.0-beta4"
    echo "  qtsrc-dir defaults to the current directory"
    exit 1
fi

FROM_BRANCH="$1"
TO_BRANCH="$2"
QTSRC_DIR="${3:-$PWD}"

KDAB_REPOS=("qtbase" "qtshadertools" "qtdeclarative" "qtwayland")
GITHUB_REMOTE="github"

if [ ! -d "$QTSRC_DIR" ]; then
    echo "Error: '$QTSRC_DIR' does not exist."
    exit 1
fi

update_repo() {
    local repo="$1"
    local repo_dir="$QTSRC_DIR/$repo"
    local to_ref
    local git_dir

    if [ ! -d "$repo_dir" ]; then
        echo "Error: '$repo_dir' does not exist."
        return 1
    fi

    # --absolute-git-dir, not --git-path: the latter is relative to the repo, but
    # the test below runs in the script's cwd.
    git_dir="$(git -C "$repo_dir" rev-parse --absolute-git-dir)" || return 1

    if [ -d "$git_dir/rebase-merge" ] || [ -d "$git_dir/rebase-apply" ]; then
        echo "Error: a rebase is already in progress in '$repo_dir'."
        return 1
    fi

    if ! git -C "$repo_dir" diff --quiet || ! git -C "$repo_dir" diff --cached --quiet; then
        echo "Error: '$repo_dir' has uncommitted changes."
        return 1
    fi

    if ! git -C "$repo_dir" remote get-url "$GITHUB_REMOTE" >/dev/null 2>&1; then
        git -C "$repo_dir" remote add "$GITHUB_REMOTE" "https://github.com/qt/$repo.git" || return 1
    fi

    git -C "$repo_dir" fetch origin || return 1
    git -C "$repo_dir" fetch --tags "$GITHUB_REMOTE" || return 1

    if ! git -C "$repo_dir" rev-parse --verify --quiet "origin/kdab/$FROM_BRANCH" >/dev/null; then
        echo "Error: branch 'kdab/$FROM_BRANCH' does not exist on origin for '$repo'."
        return 1
    fi

    if git -C "$repo_dir" rev-parse --verify --quiet "refs/tags/$TO_BRANCH" >/dev/null; then
        to_ref="refs/tags/$TO_BRANCH"
    elif git -C "$repo_dir" rev-parse --verify --quiet "$GITHUB_REMOTE/$TO_BRANCH" >/dev/null; then
        to_ref="$GITHUB_REMOTE/$TO_BRANCH"
    else
        echo "Error: '$TO_BRANCH' is neither a tag nor a branch on $GITHUB_REMOTE for '$repo'."
        return 1
    fi

    # --no-track: without it the new branch tracks kdab/<from-branch> and a bare
    # 'git push' in the repo would overwrite the branch we copied the patches from.
    git -C "$repo_dir" checkout --no-track -B "kdab/$TO_BRANCH" "origin/kdab/$FROM_BRANCH" || return 1

    echo "Patches to copy onto $TO_BRANCH:"
    git -C "$repo_dir" log --oneline --reverse "$to_ref..HEAD" || return 1

    git -C "$repo_dir" rebase "$to_ref" || return 2
}

CONFLICTED_REPOS=()
FAILED_REPOS=()
PUSH_COMMANDS=()

for repo in "${KDAB_REPOS[@]}"; do
    echo "=== $repo ==="

    update_repo "$repo" && rc=0 || rc=$?
    case "$rc" in
        0) PUSH_COMMANDS+=("git -C '$QTSRC_DIR/$repo' push origin 'kdab/$TO_BRANCH'") ;;
        2) CONFLICTED_REPOS+=("$repo") ;;
        *) FAILED_REPOS+=("$repo") ;;
    esac
done

if [ ${#PUSH_COMMANDS[@]} -gt 0 ]; then
    echo
    echo "=== Rebased, review then push ==="
    printf '%s\n' "${PUSH_COMMANDS[@]}"
fi

if [ ${#CONFLICTED_REPOS[@]} -gt 0 ]; then
    echo
    echo "=== Conflicted, left mid-rebase ==="
    # Re-running the script would reset kdab/<to-branch> back to origin and drop
    # the resolution, so hand over the push command rather than a re-run.
    for repo in "${CONFLICTED_REPOS[@]}"; do
        echo "$repo: resolve, then 'git -C \"$QTSRC_DIR/$repo\" rebase --continue', then:"
        echo "  git -C '$QTSRC_DIR/$repo' push origin 'kdab/$TO_BRANCH'"
    done
fi

if [ ${#FAILED_REPOS[@]} -gt 0 ]; then
    echo
    echo "=== Skipped, see errors above: ${FAILED_REPOS[*]} ==="
fi

if [ ${#CONFLICTED_REPOS[@]} -gt 0 ] || [ ${#FAILED_REPOS[@]} -gt 0 ]; then
    exit 1
fi
