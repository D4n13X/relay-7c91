#!/bin/sh
# Compatibility link: all plugin repositories are managed by os-d4n13x-repo.
main() {
    set -eu
    hfu_installer=$(mktemp -d /tmp/d4n13x-repo-bootstrap.XXXXXX)
    trap 'rm -rf "$hfu_installer"' EXIT
    trap 'exit 1' HUP INT TERM
    fetch -q -o "$hfu_installer/install-repo.sh" https://d4n13x.github.io/relay-7c91/install-repo.sh
    sh "$hfu_installer/install-repo.sh"
}
main "$@"
