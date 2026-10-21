#!/bin/sh
# Enable this project's signed update feed. Does not install or enable the plugin.
# All work is inside main so a truncated piped download cannot execute a partial body.
main() {
    set -eu
    [ "$(id -u)" = 0 ] || { echo 'Run this installer as root.' >&2; exit 1; }
    [ "$(uname -m)" = amd64 ] || { echo 'Requires OPNsense amd64.' >&2; exit 1; }
    case "$(opnsense-version -v)" in
        26.7|26.7.*|26.7_*) ;;
        *) echo 'Requires OPNsense 26.7.' >&2; exit 1 ;;
    esac
    [ "$(pkg config ABI)" = 'FreeBSD:15:amd64' ] || { echo 'Unsupported package ABI.' >&2; exit 1; }
    umask 077
    hfu_work=$(mktemp -d /tmp/hetzner-repo-install.XXXXXX)
    trap 'rm -rf "$hfu_work"' EXIT
    trap 'exit 1' HUP INT TERM
    hfu_package=os-hetzner-firewall-updater-repo
    hfu_repository=HetznerFirewallUpdater
    fetch -q -o "$hfu_work/repo.pkg" 'https://d4n13x.github.io/relay-7c91/projects/hetzner-firewall-updater/FreeBSD:15:amd64/26.7/os-hetzner-firewall-updater-repo-0.1.1.pkg'
    [ "$(sha256 -q "$hfu_work/repo.pkg")" = 'eff3b9ab3281797a8ed0156b80185ba8ef4c479466e600c291c44f033d52d59c' ] || {
        echo 'Repository package checksum mismatch; nothing installed.' >&2; exit 1;
    }
    if pkg info -e "$hfu_package"; then
        hfu_compare=$(pkg version -t "$(pkg query '%v' "$hfu_package")" '0.1.1')
        case "$hfu_compare" in
            '<') pkg add "$hfu_work/repo.pkg" ;;
            '='|'>') echo 'Repository package is already installed; checking integrity.' ;;
            *) echo 'Cannot compare installed repository version.' >&2; exit 1 ;;
        esac
    else
        pkg add "$hfu_work/repo.pkg"
    fi
    pkg check -s "$hfu_package"
    openssl pkey -pubin -in /usr/local/etc/pkg/keys/hetzner-firewall-updater.pub -outform DER > "$hfu_work/public.der"
    [ "$(sha256 -q "$hfu_work/public.der")" = '71540faf358ef598ec86ec0b0e4a9e804b8a0bf80406509faf30f55bec8ecdfa' ] || {
        echo 'Installed repository signing key does not match pinned trust.' >&2; exit 1;
    }
    # pkg update can exit zero on a signature failure. Require a populated fresh catalog.
    mkdir "$hfu_work/repos" "$hfu_work/db" "$hfu_work/cache"
    cp /usr/local/etc/pkg/repos/HetznerFirewallUpdater.conf "$hfu_work/repos/"
    pkg -o "REPOS_DIR=$hfu_work/repos" -o "PKG_DBDIR=$hfu_work/db" -o "PKG_CACHEDIR=$hfu_work/cache" update -f -r "$hfu_repository"
    pkg -o "REPOS_DIR=$hfu_work/repos" -o "PKG_DBDIR=$hfu_work/db" -o "PKG_CACHEDIR=$hfu_work/cache" rquery -r "$hfu_repository" '%n' > "$hfu_work/catalog"
    grep -Fx 'os-hetzner-firewall-updater' "$hfu_work/catalog" >/dev/null || {
        echo 'Signed catalog could not be authenticated; stopping.' >&2; exit 1;
    }
    pkg update -f -r "$hfu_repository"
    if [ "$(pkg query '%R' "$hfu_package")" = unknown-repository ]; then
        pkg annotate -y -A "$hfu_package" repository "$hfu_repository"
    fi
    echo 'Hetzner Firewall Updater repository is installed and enabled for future updates.'
    echo 'Install the plugin with:'
    echo 'pkg install -r HetznerFirewallUpdater os-hetzner-firewall-updater'
}
main "$@"
