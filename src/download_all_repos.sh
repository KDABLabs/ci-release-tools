#!/bin/bash

# Downloads all repos of our organization, 11 GB (as of 2025)

OUTPUT_DIR=$(pwd)

download_repos() {
    mkdir -p $OUTPUT_DIR/$1 && cd $OUTPUT_DIR/$1
    gh repo list "$1" --limit 1000 --json nameWithOwner --jq '.[].nameWithOwner' | xargs -I {} git clone "git@github.com:{}.git"
}

download_repos KDAB
download_repos KDABLabs
