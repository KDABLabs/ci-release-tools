#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: MIT

# Scripts related to GitHub

# Examples:
# $ gh_utils.py --get-latest-release=KDAB/KDDockWidgets
# v2.1.0

import json
import argparse
import uuid
from utils import get_projects, repo_exists, run_command, run_command_with_output, run_command_silent, tag_for_version, get_project, get_submodule_builtin_dependencies
import utils
from version_utils import is_numeric, previous_version, get_current_version_in_cmake
from changelog_utils import get_changelog


def get_latest_release_tag_in_github(repo, repo_path, main_branch, via_tag=False):
    """
    Returns the tag of latest release
    repo is for example 'KDAB/KDReports'. If None, then gh will be run inside the repo at cwd.
    If via_tag is true, we'll try git locally, instead of gh release, which doesn't require local repo.
    """

    if via_tag:
        cmd = f"git -C {repo_path} describe --tags --abbrev=0 origin/{main_branch}"
        return run_command_with_output(cmd).strip()

    # Via gh release:
    try:
        repo_arg = f"--repo {repo}" if repo else ""

        cmd = f"gh release list {repo_arg} --limit 1"
        lines = run_command_with_output(cmd, repo_path).split('\n')
        if not lines or lines == ['']:
            return None

        # print(f"lines={lines}, cmd={cmd}, cwd={cwd}")

        # example:
        # TITLE            TYPE    TAG NAME         PUBLISHED
        # KDReports 2.3.0  Latest  kdreports-2.3.0  about 2 months ago
        version = lines[0].split('\t')
        if len(version) < 3:
            print(f"get_latest_release_tag_in_github: could not parse {lines}")
            return None
        version = version[2]
    except Exception as e:
        print(f"Failed to get latest release: {e}")
        return None
    return version


def tag_exists(repo, tag):
    return run_command_silent(f"gh api repos/KDAB/{repo}/git/refs/tags/{tag}")


def sha1_for_tag(repo_path, tag):
    """
    uses gh to create a tag
    """
    output = run_command_with_output(
        f"git -C {repo_path} rev-parse {tag}^{{commit}}")
    return output.strip()


def create_tag(proj_name, tag, sha1):
    cmd = f"gh api -X POST /repos/KDAB/{proj_name}/git/refs -f ref=refs/tags/{tag} -f sha={sha1}"
    return run_command(cmd)


def create_tag_via_git(proj_name, version, sha, repo_path):
    """
    uses git to create a sha
    """
    tag = tag_for_version(proj_name, version)
    if tag_exists(proj_name, tag):
        existing_tagged_sha1 = sha1_for_tag(repo_path, tag)
        if sha != existing_tagged_sha1:
            print(
                f"Tag {tag} already exists but points to different sha {sha} != {existing_tagged_sha1}!")
            return False
    else:
        cmd = f"git -C {repo_path} tag -a {tag} {sha} -m \"{proj_name} {tag}\""
        if not run_command(cmd):
            print(f"Failed to create tag {tag}")
            return False

    if not run_command(f"git -C {repo_path} push origin {tag}"):
        print(f"Failed to push tag {tag}")
        return False
    return True


def download_tarball(repo, tag, version):
    return run_command_silent(f"curl -L -o {repo.lower()}-{version}.tar.gz https://github.com/KDAB/{repo}/archive/refs/tags/{tag}.tar.gz")


def tarball_has_integrity(filename):
    return run_command_silent(f"tar tzf {filename}")


def sign_file(filename):
    return run_command(f"gpg --local-user \"KDAB Products\" --armor --detach-sign {filename}")


def can_bump_to(proj_name, version, sha1, check_ci=True):
    """
    Returns True if we can bump to the specified version
    Reasons not to, include:
        - The previous semantic tag doesn't exist
        - Version in CMake doesn't match
        - Changelog entry doesn't exist
        - CI has failures
    """
    if not is_numeric(version):
        print("Do not pass versions with prefixes")
        return False

    prev = previous_version(version)
    proj = get_project(proj_name)
    tag_prefix = proj['tag_prefix']

    new_tag = f"{tag_prefix}{version}"
    prev_tag = f"{tag_prefix}{prev}"
    if prev != '0.0.0' and not tag_exists(proj_name, prev_tag):
        print(f"Error: Can't tag {new_tag} without {prev_tag}")
        return False

    if not get_changelog(proj_name, version, sha1):
        print(f"Error: No changelog found for version {version}")
        return False

    cur_cmake_version = get_current_version_in_cmake(proj_name, sha1)
    if cur_cmake_version != version:
        print(
            f"You need to bump the version in CMakeLists.txt, currently it's at {cur_cmake_version}")
        return False

    if check_ci:
        ci_in_progress, ci_completed, ci_failed = ci_run_status(
            proj_name, sha1)
        if ci_in_progress:
            print("error: CI is still running, please try again later")
            return False

        if ci_failed:
            print(f"error: CI has failed jobs for sha1 {sha1}")
            return False

        if not ci_completed:
            print(f"error: CI doesn't have completed runs for {sha1}")
            return False

    return True


def release_exists(repo, tag):
    return run_command_silent(f"gh release view {tag} --repo KDAB/{repo}")


def create_release(repo, version, sha1, notes, repo_path, should_sign):
    tag = tag_for_version(repo, version)
    if not repo_exists(repo):
        print(f"error: unknown repo {repo}, check releasing.toml")
        return False

    if not can_bump_to(repo, version, sha1):
        print("error: Project not ready to be tagged.")
        return False

    if not create_tag_via_git(repo, version, sha1, repo_path):
        print("error: Could not create tag")
        return False

    if release_exists(repo, tag):
        print(f"error: release {tag} already exists in {repo}")
        return False

    if not download_tarball(repo, tag, version):
        print(f"error: failed to download tarball from repo {repo}")
        return False

    tarball = f"{repo}-{version}.tar.gz".lower()
    if not tarball_has_integrity(tarball):
        print(f"error: Tarball {tarball} is corrupted")
        return False

    files_to_upload = ""
    if should_sign:
        if not sign_file(tarball):
            print(f"error: Failed to sign {tarball}")
            return False
        files_to_upload = f"{tarball}.asc {tarball}"
    else:
        files_to_upload = f"{tarball}"

    cmd = f"gh release create {tag} " \
        f"--repo KDAB/{repo} " \
        f'--title "Release {tag}" ' \
        f'--notes "{notes}" ' + files_to_upload

    if not run_command(cmd):
        print("error: Could not create release")
        return False

    return True


def sign_and_upload(proj_name, version):
    """
    Since GH actions can't sign, here's a function that signs and uploads
    To be run locally, example:
        ./src/sign_and_upload.py --repo KDDockWidgets --version 2.2.1
    """
    tag = tag_for_version(proj_name, version)
    if not download_tarball(proj_name, tag, version):
        print(f"error: failed to download tarball for {proj_name}")
        return False

    tarball = f"{proj_name}-{version}.tar.gz".lower()
    if not sign_file(tarball):
        print(f"error: Failed to sign {tarball}")
        return False

    if not run_command(f"gh release upload -R KDAB/{proj_name} {tag} {tarball}.asc"):
        print("error: Could not create release")
        return False

    return True


def ci_run_status(proj_name, sha1):
    output = run_command_with_output(
        f"gh run list -R KDAB/{proj_name} --commit {sha1} --json status,name")

    try:
        output = json.loads(output)
    except Exception as e:
        print(f"Failed to parse JSON: {output}")
        raise e

    filtered_data = [
        item for item in output if item["name"] != "Create release"]

    in_progress = any(item["status"] ==
                      "in_progress" for item in filtered_data)
    completed = any(item["status"] == "completed" for item in filtered_data)

    failure_states = ["failure", "timed_out", "cancelled"]
    failed = any(item["status"] in failure_states for item in filtered_data)

    if in_progress or completed or failed:
        print(output)

    return in_progress, completed, failed


def get_head_version(repo_path, sha1='HEAD'):
    '''
    Returns the tagged version of a repo located at repo_path.

    Runs git-describe on a git repo, for example:
        git -C ../KDStateMachineEditor/3rdparty/graphviz describe --tags HEAD
        which returns: 11.0.0-546-gb4650ee85
    This won't update/init submodules, be sure to not run on an old checkout.
    '''
    return run_command_with_output(f"git -C {repo_path} describe --abbrev=0 --tags {sha1}").strip()


def checkout_randomly_named_branch(repo_path, prefix):
    branch = f"{prefix}-{str(uuid.uuid4())}"
    if run_command(f"git -C {repo_path} checkout -B {branch}"):
        return branch
    return None


def get_current_fetchcontent_sha1s(repo_path, proj_name, dep_name=None):
    '''
    Returns the current shas of our fetchcontent dependencies.
    Example:
        shas = gh_utils.get_current_fetchcontent_sha1s(kdutils_dir, 'KDUtils')
     would return: [{'name': 'fmt', 'repo': 'https://github.com/fmtlib/fmt.git', 'sha1': 'e69e5f977d458f2650bb346dadf2ad30c5320281'}, (etc...) ]
    '''

    deps = utils.get_fetchcontent_builtin_dependencies(proj_name)
    if not deps.items():
        return []

    result = []
    for key, dep in deps.items():

        if dep_name and dep_name != key:
            continue

        cmake_filename = repo_path + '/' + dep['fetchcontent_path']
        with open(cmake_filename, 'r', encoding='UTF-8') as file:
            cmake_code = file.read()
            fetch_content = utils.get_fetchcontents_from_code(cmake_code, key)[
                0]
            fetch_content['main_branch'] = dep['main_branch']
            fetch_content['fetchcontent_path'] = dep['fetchcontent_path']
            result.append(fetch_content)
    return result


def get_fetchcontent_versions(repo_path, proj_name, dep_name=None):
    deps = get_current_fetchcontent_sha1s(repo_path, proj_name, dep_name)
    result = []

    for dep in deps:
        def get_versions(dep_repo_path):
            current = get_head_version(dep_repo_path, dep['sha1'])
            latest = None
            latest_sha1 = None
            if current:
                latest = get_latest_release_tag_in_github(
                    None, dep_repo_path, dep['main_branch'], True)
                latest_sha1 = run_command_with_output(
                    f"git -C {dep_repo_path} rev-parse {latest}").strip()

            return (current, latest, latest_sha1)

        current_version = None
        latest_version = None
        latest_version_sha1 = None
        clone_result = utils.clone_repo(dep['repo'], get_versions)
        if clone_result and isinstance(clone_result, tuple):
            current_version, latest_version, latest_version_sha1 = clone_result

        result.append(
            {'name': dep['name'],
             'fetchcontent_path': dep['fetchcontent_path'],
             'current_version': current_version,
             'current_version_sha1': dep['sha1'],
             'latest_version': latest_version,
             'latest_version_sha1': latest_version_sha1
             })

    return result


def get_submodule_versions(master_repo_path, proj_name, submodule_name=None):
    '''
        returns the list of submodule current and latest versions for give project
        example:
            get_submodule_versions('../KDStateMachineEditor', 'KDStateMachineEditor')
            returns: [
                {
                    'name': 'graphviz',
                    'current_version': '11.0.0',
                    'latest_version': '12.2.1'
                }
            ]
        If submodule_name is set, returns only versions for that particular submodule
    '''
    deps = get_submodule_builtin_dependencies(proj_name)
    if not deps.items():
        return []

    result = []
    for key, dep in deps.items():
        if submodule_name and key != submodule_name:
            continue

        repo_path = master_repo_path + '/' + dep['submodule_path']
        submodule_main_branch = dep.get('main_branch', 'main')
        latest_version = get_latest_release_tag_in_github(
            None, repo_path, submodule_main_branch, True)
        current_version = get_head_version(repo_path)

        result.append({
            'submodule_name': key,  # the key in releasing.yml
            'submodule_path': dep['submodule_path'],
            'current_version': current_version,
            'latest_version': latest_version
        })
    return result


def print_submodule_versions(repo_paths):
    '''
    prints the versions of submodules used by all KD* projects
    This won't update/init submodules, be sure to not run on an old checkout.
    '''
    projs = get_projects()
    for proj in projs:
        versions = get_submodule_versions(repo_paths + '/' + proj, proj)
        for version in versions:
            latest_version = version['latest_version']
            current_version = version['current_version']
            submodule_path = version['submodule_path']

            if latest_version == current_version or current_version == 'latest':
                print(
                    f"    {submodule_path}: {current_version}")
            elif latest_version:
                print(
                    f"    {submodule_path}: {current_version} ({latest_version} is available)")
            else:
                print(
                    f"    {submodule_path}: {current_version} -> ????")


def update_dependency(proj_name, dep_name, sha1, repo_path, remote, branch):
    proj = get_project(proj_name)
    if 'dependencies' not in proj:
        print(
            f"Project {proj} does not have any dependencies, check releasing.toml")
        return False

    if not branch:
        branch = proj.get('main_branch', 'main')

    deps = proj['dependencies']
    dep = deps[dep_name]
    if 'submodule_path' in dep:
        return update_submodule(proj_name, dep_name, sha1, repo_path, remote, branch)

    if 'fetchcontent_path' in dep:
        return update_fetchcontent(proj_name, dep_name, sha1, repo_path, remote, branch)

    print("Dependency is neither a submodule or a FetchContent, check releasing.toml")
    return False


def update_fetchcontent(proj_name, dep_name, sha1, repo_path, remote, branch):
    '''
    Like update_submodule() but bumps a FetchContent dependency.
    '''

    versions = get_fetchcontent_versions(repo_path, proj_name, dep_name)
    versions = versions[0]
    tag_name = None
    current_sha1 = versions['current_version_sha1']

    if not sha1:
        if versions['current_version'] == versions['latest_version'] or versions['current_version'] == 'latest':
            # already latest
            return True

        sha1 = versions['latest_version_sha1']
        tag_name = versions['latest_version']

    cmake_filename = repo_path + '/' + versions['fetchcontent_path']
    if not utils.set_fetchcontent_sha1(cmake_filename, current_sha1, sha1, tag_name):
        print(f'Error while editing {cmake_filename}')
        return False

    return False


def update_submodule(proj_name, submodule_name, sha1, repo_path, remote, branch):
    proj = get_project(proj_name)

    deps = proj['dependencies']

    submodule = deps[submodule_name]
    submodule_path = repo_path + '/' + submodule['submodule_path']
    versions = get_submodule_versions(repo_path, proj_name, submodule_name)
    if len(versions) != 1:
        print("Could not get submodule versions")
        return False

    versions = versions[0]

    if not sha1:
        if versions['current_version'] == versions['latest_version'] or versions['current_version'] == 'latest':
            # already latest
            return True

        sha1 = versions['latest_version']

    if not run_command(f"git -C {repo_path} checkout {branch}"):
        return False

    tmp_branch = checkout_randomly_named_branch(repo_path, "gh-actions")
    if not tmp_branch:
        return False

    if not run_command(f"git -C {submodule_path} checkout {sha1}"):
        return False

    if not run_command(f"git -C {repo_path} add {submodule['submodule_path']}"):
        return False

    commit_msg = f"\"Bump {submodule_name} from {versions['current_version']} to {sha1}\""

    if not run_command(f"git -C {repo_path} commit --author \"KDAB GitHub Actions <gh@kdab>\" -m {commit_msg}"):
        return False

    if not run_command(f"git -C {repo_path} push {remote} {tmp_branch}"):
        return False

    if not run_command(f"git -C {repo_path} push --set-upstream {remote} {tmp_branch}"):
        return False

    if not run_command(f"gh pr create -R KDAB/{proj_name} --base {branch} -H {tmp_branch} --title {commit_msg} --body \"Automatically created via GH action.\""):
        return False

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--get-latest-release', metavar='REPO',
                        help="returns latest release for a repo")
    args = parser.parse_args()
    if args.get_latest_release:
        print(get_latest_release_tag_in_github(
            args.get_latest_release, None, None))

# print_submodule_versions('..')
