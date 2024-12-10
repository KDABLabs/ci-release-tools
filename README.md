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
./src/create_release.py --repo KDAlgorithms --tag 1.4 --releasenotes 1.4_notes.txt
```
