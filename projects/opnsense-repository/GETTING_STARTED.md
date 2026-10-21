# D4n13X plugin repository

One native repository named **D4n13X**, configured by **os-d4n13x-repo**, supplies
all plugins and their updates on OPNsense 26.7 amd64. Run as root:

```sh
fetch -qo - https://d4n13x.github.io/relay-7c91/install-repo.sh | sh
pkg install -r D4n13X os-gamecache
pkg install -r D4n13X os-hetzner-firewall-updater
```

Install whichever plugins you need. The bootstrap does not enable either plugin.
Version 0.4.5 consolidates the earlier split feeds into the existing D4n13X
catalog, preserving the latest Game Cache feed URL and existing signing trust. It preserves plugin settings,
backs up previous bootstrap packages/configuration privately, and removes obsolete
centrally owned Hetzner source/key files through the native package upgrade.
The old standalone Hetzner bootstrap is migrated too.

## Update existing beta installations

```sh
fetch -qo - https://d4n13x.github.io/relay-7c91/install-repo.sh | sh
pkg update -f -r D4n13X
pkg install -r D4n13X os-hetzner-firewall-updater
pkg query '%n %v' os-hetzner-firewall-updater
```

The updater should report 0.1.2 or newer; refresh its page. Version 0.1.2 fixes
native settings/interface reads after selecting an interface. No settings reset or
reboot is required. Save a private configuration backup before package changes.

## Maintainers

Central bootstrap versions are independent of plugin versions. Release a combined
signed catalog containing the latest exact artifacts for both plugins and the
bootstrap. Never rebuild the bootstrap as part of an individual plugin release.
Preserve versioned bytes and URLs, other project files, and the shared README.
Publication must reject stale upstream state and preserve the other plugin.
Keep signing keys local and outside checkouts. Old project feed URLs remain for
compatibility; new installations use only D4n13X. See each plugin's guide for its
configuration, beta scope and qualification results.
