# ci-release-tools

Scripts related to making releases and GitHub actions.

## gh_utils.py

Scripts related to GitHub, for example:

### Get latest releases

```bash
./src/gh_utils.py --get-latest-release=KDAB/KDAlgorithms
```

### Create a release

```bash
./src/create_release.py --repo KDDockWidgets --version 2.2.1 --sha1 3aaccddc00a11a643e0959a24677838993de15ac --repo-path path/to/KDDockWidgets/
```

### Testing Changelog related code

```bash
./src/create_release.py --only-print-changelog --repo KDDockWidgets --version 2.2.1 --sha1 3aaccddc00a11a643e0959a24677838993de15ac --repo-path path/to/KDDockWidgets/
```

### Sign and upload tarball+signature

```bash
python3 src/sign_and_upload.py --repo KDDockWidgets --version 2.2.3
```

## Get versions of submodules or FetchContent dependencies

```bash
python3 ci-release-tools/src/update_dependencies.py --print-dependency-versions --proj-name KDStateMachineEditor --repo-path KDStateMachineEditor
```
