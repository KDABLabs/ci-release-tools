#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Checks that the default branch (main/master) of the projects in releasing.toml
# requires pull requests, either via classic branch protection or a ruleset, and
# that admins can't override it (no direct pushes).
# With --all, checks all repos of our GitHub organizations instead.
# Prints the offending ones and exits with 1 if there are any.
#
# Requires the gh CLI, authenticated with admin access to the repos.
#
# example usage:
# ./src/check_branch_protection.py
# ./src/check_branch_protection.py --all
# ./src/check_branch_protection.py --all --org KDAB

import argparse
import json
import subprocess
import sys

import utils

DEFAULT_ORGS = ["KDAB", "KDABLabs"]


def gh_api(path):
    """Returns the parsed json, or None if the request failed (e.g. 404)."""
    p = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if p.returncode != 0:
        return None
    return json.loads(p.stdout)


def list_repos(org, include_archived):
    p = subprocess.run(
        ["gh", "repo", "list", org, "--limit", "1000", "--json",
         "nameWithOwner,defaultBranchRef,isArchived,isFork"],
        capture_output=True, text=True)
    if p.returncode != 0:
        print(f"Failed to list repos of {org}: {p.stderr.strip()}", file=sys.stderr)
        sys.exit(2)

    repos = json.loads(p.stdout)
    if not include_archived:
        repos = [r for r in repos if not r["isArchived"]]
    return repos


ADMIN_REPO_ROLE_ID = 5


def ruleset_admin_can_bypass(rule):
    """Whether repo/org admins can bypass the ruleset the given rule comes from.
    Returns None if the ruleset couldn't be read."""
    rid = rule["ruleset_id"]
    source = rule["ruleset_source"]
    if rule.get("ruleset_source_type") == "Organization":
        ruleset = gh_api(f"orgs/{source}/rulesets/{rid}")
    else:
        ruleset = gh_api(f"repos/{source}/rulesets/{rid}")

    if ruleset is None:
        return None

    for actor in ruleset.get("bypass_actors") or []:
        # "pull_request" mode only allows bypassing the PR's approval, not pushing directly
        if actor.get("bypass_mode") != "always":
            continue
        if actor["actor_type"] == "OrganizationAdmin":
            return True
        if actor["actor_type"] == "RepositoryRole" and actor.get("actor_id") == ADMIN_REPO_ROLE_ID:
            return True
    return False


OK, ADMIN_BYPASS, NO_PR = range(3)

# Green check, yellow and red cross
STATUS_ICONS = {
    OK: "\033[32m\u2714\033[0m",
    ADMIN_BYPASS: "\033[33m\u2718\033[0m",
    NO_PR: "\033[31m\u2718\033[0m",
}


def check_branch(name_with_owner, branch):
    """Returns (status, problem). problem is None if the branch requires a PR and admins can't override it."""
    # Each entry is "can admins bypass it?" for one mechanism that requires PRs.
    # None means unknown.
    pr_enforcers = {}

    # Classic branch protection
    protection = gh_api(f"repos/{name_with_owner}/branches/{branch}/protection")
    if protection and "required_pull_request_reviews" in protection:
        pr_enforcers["branch protection"] = not protection.get("enforce_admins", {}).get("enabled", False)

    # Rulesets. This endpoint only returns active rules that apply to the branch.
    rules = gh_api(f"repos/{name_with_owner}/rules/branches/{branch}") or []
    for rule in rules:
        if rule["type"] == "pull_request":
            key = f"ruleset {rule['ruleset_id']}"
            if key not in pr_enforcers:
                pr_enforcers[key] = ruleset_admin_can_bypass(rule)

    if not pr_enforcers:
        return NO_PR, "doesn't require pull requests"

    # Admins are blocked as long as one mechanism blocks them
    if any(bypass is False for bypass in pr_enforcers.values()):
        return OK, None

    if any(bypass is None for bypass in pr_enforcers.values()):
        return ADMIN_BYPASS, "couldn't determine if admins can bypass the pull request requirement"

    return ADMIN_BYPASS, "admins can bypass the pull request requirement"


def releasing_toml_repos():
    """Returns (nameWithOwner, default branch) for each project in releasing.toml"""
    repos = []
    for proj_name in utils.get_projects():
        name = f"KDAB/{proj_name}"
        info = gh_api(f"repos/{name}")
        if info is None:
            print(f"Failed to query {name}", file=sys.stderr)
            sys.exit(2)
        repos.append((name, info["default_branch"]))
    return repos


def org_repos(orgs, include_archived, include_forks):
    """Returns (nameWithOwner, default branch) for each repo of the given orgs"""
    repos = []
    for org in orgs:
        for repo in list_repos(org, include_archived):
            if repo["isFork"] and not include_forks:
                continue
            ref = repo["defaultBranchRef"]
            if not ref:  # empty repo
                continue
            repos.append((repo["nameWithOwner"], ref["name"]))
    return repos


def main():
    parser = argparse.ArgumentParser(description="Checks branch protection of main/master in the releasing.toml repos")
    parser.add_argument("--all", action="store_true", help="Check all repos of our organizations instead of just releasing.toml")
    parser.add_argument("--org", action="append", help=f"Organization to check with --all, can be repeated. Default: {DEFAULT_ORGS}")
    parser.add_argument("--include-archived", action="store_true", help="With --all, also check archived repos")
    parser.add_argument("--include-forks", action="store_true", help="With --all, also check forks")
    args = parser.parse_args()

    if not args.all and (args.org or args.include_archived or args.include_forks):
        parser.error("--org, --include-archived and --include-forks require --all")

    if args.all:
        repos = org_repos(args.org or DEFAULT_ORGS, args.include_archived, args.include_forks)
    else:
        repos = releasing_toml_repos()

    unprotected = []
    for name, branch in repos:
        if branch not in ("main", "master"):
            print(f"Skipping {name}: default branch is '{branch}'", file=sys.stderr)
            continue

        status, problem = check_branch(name, branch)
        line = f"{name} ({branch})"
        if problem:
            line += f": {problem}"
            unprotected.append(line)
        print(f"{STATUS_ICONS[status]} {line}", flush=True)

    if unprotected:
        print("\nRepos with insufficient branch protection:")
        for r in sorted(unprotected):
            print(f"  {r}")
        return 1

    print("\nAll repos require PRs, with no admin override")
    return 0


if __name__ == "__main__":
    sys.exit(main())
