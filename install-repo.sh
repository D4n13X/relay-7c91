#!/bin/sh
# One shared bootstrap for all D4n13X OPNsense plugin feeds.
main() {
    set -eu
    [ "$(id -u)" = 0 ] || { echo 'Run this installer as root.' >&2; exit 1; }
    [ "$(uname -m)" = amd64 ] || { echo 'Requires OPNsense amd64.' >&2; exit 1; }
    case "$(opnsense-version -v)" in
        26.7|26.7.*|26.7_*) ;;
        *) echo 'Requires OPNsense 26.7.' >&2; exit 1 ;;
    esac
    [ "$(pkg config ABI)" = 'FreeBSD:15:amd64' ] || exit 1
    umask 077
    d4_work=$(mktemp -d /tmp/d4n13x-repo-install.XXXXXX)
    trap 'rm -rf "$d4_work"' EXIT
    trap 'exit 1' HUP INT TERM
    fetch -q -o "$d4_work/repo.pkg" 'https://d4n13x.github.io/relay-7c91/FreeBSD:15:amd64/26.7/os-d4n13x-repo-0.4.4.pkg'
    [ "$(sha256 -q "$d4_work/repo.pkg")" = 'c4d15b313542feb55ef12e6535de7596fc405167d976439dc4bd088e054637a0' ] || {
        echo 'Central repository package checksum mismatch; nothing changed.' >&2; exit 1;
    }
    d4_install=1
    if pkg info -e os-d4n13x-repo; then
        d4_compare=$(pkg version -t "$(pkg query '%v' os-d4n13x-repo)" '0.4.4')
        case "$d4_compare" in '='|'>') d4_install=0 ;; '<') ;; *) exit 1 ;; esac
    fi
    if pkg info -e os-hetzner-firewall-updater-repo; then
        if [ "$d4_install" = 0 ]; then
            echo 'Conflicting legacy and current bootstrap packages: contact your beta coordinator.' >&2
            exit 1
        fi
        d4_backup=$(mktemp -d /root/d4n13x-repo-migration.XXXXXX)
        cp -p /conf/config.xml "$d4_backup/config.xml"
        pkg create -o "$d4_backup" os-hetzner-firewall-updater-repo
        d4_legacy_version=$(pkg query '%v' os-hetzner-firewall-updater-repo)
        echo "Migrating the legacy Hetzner bootstrap; private backup: $d4_backup"
        pkg delete -y os-hetzner-firewall-updater-repo
        if ! pkg add "$d4_work/repo.pkg"; then
            echo 'Central install failed; restoring the previous Hetzner bootstrap.' >&2
            pkg add "$d4_backup/os-hetzner-firewall-updater-repo-$d4_legacy_version.pkg" || true
            exit 1
        fi
    elif [ "$d4_install" = 1 ]; then
        pkg add "$d4_work/repo.pkg"
    else
        echo 'Shared repository bootstrap is already installed.'
    fi
    pkg check -s os-d4n13x-repo
    for d4_pair in 'gamecache.pub:994304f193330956c0892ba655068253821d0c5830e8bfc8cb252e2707d6e91c' 'hetzner-firewall-updater.pub:71540faf358ef598ec86ec0b0e4a9e804b8a0bf80406509faf30f55bec8ecdfa'; do
        d4_key=${d4_pair%%:*}
        d4_fingerprint=${d4_pair#*:}
        openssl pkey -pubin -in "/usr/local/etc/pkg/keys/$d4_key" -outform DER > "$d4_work/key.der"
        [ "$(sha256 -q "$d4_work/key.der")" = "$d4_fingerprint" ] || {
            echo 'Installed signing key does not match pinned trust.' >&2; exit 1;
        }
    done
    mkdir "$d4_work/repos" "$d4_work/db" "$d4_work/cache"
    cp /usr/local/etc/pkg/repos/GameCache.conf "$d4_work/repos/"
    cp /usr/local/etc/pkg/repos/HetznerFirewallUpdater.conf "$d4_work/repos/"
    for d4_repo in D4n13X HetznerFirewallUpdater; do
        pkg -o "REPOS_DIR=$d4_work/repos" -o "PKG_DBDIR=$d4_work/db" -o "PKG_CACHEDIR=$d4_work/cache" update -f -r "$d4_repo"
        pkg -o "REPOS_DIR=$d4_work/repos" -o "PKG_DBDIR=$d4_work/db" -o "PKG_CACHEDIR=$d4_work/cache" rquery -r "$d4_repo" '%n' > "$d4_work/catalog"
        case "$d4_repo" in D4n13X) d4_expected=os-d4n13x-repo ;; *) d4_expected=os-hetzner-firewall-updater ;; esac
        grep -Fx "$d4_expected" "$d4_work/catalog" >/dev/null || {
            echo 'Signed catalog could not be authenticated.' >&2; exit 1;
        }
        pkg update -f -r "$d4_repo"
    done
    if [ "$(pkg query '%R' os-d4n13x-repo)" = unknown-repository ]; then
        pkg annotate -y -A os-d4n13x-repo repository D4n13X
    fi
    echo 'os-d4n13x-repo is installed: shared signed feeds are enabled for all D4n13X plugins.'
}
main "$@"
