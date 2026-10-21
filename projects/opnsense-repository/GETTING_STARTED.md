# Shared D4n13X OPNsense repository

Use one package, **os-d4n13x-repo**, for all D4n13X plugin feeds and future updates.
For OPNsense 26.7 amd64, run as root:

```sh
fetch -qo - https://d4n13x.github.io/relay-7c91/install-repo.sh | sh
```

Then install the plugin you want:

```sh
pkg install -r D4n13X os-gamecache
pkg install -r HetznerFirewallUpdater os-hetzner-firewall-updater
```

The bootstrap owns both feed configurations and their independent signing keys.
Existing Game Cache trust and its D4n13X repository identifier are preserved.
Version 0.4.2 adds Hetzner trust to the same shared package. It does not change,
install or enable either plugin. Updates remain available through normal native
package/firmware catalog refreshes.

The installer verifies its pinned package checksum and both public fingerprints,
and authenticates fresh catalogs. It migrates the obsolete standalone
os-hetzner-firewall-updater-repo package into the central package, retaining a
private rollback package/configuration under /root. The updater itself and saved
settings are retained. Do not remove the shared os-d4n13x-repo package when
removing one plugin: it supplies update trust for the others too.

Game Cache's guide remains at ../gamecache/GETTING_STARTED.md; the Hetzner guide
is ../hetzner-firewall-updater/GETTING_STARTED.md. Plugin qualification and setup
requirements are described in their guides.

Central repository versions are independent of plugin versions. Maintainers must
reuse the exact current central bootstrap in plugin release catalogs, and must
not rebuild an older single-feed bootstrap as part of a plugin release. Public
versioned package URLs are immutable. This directory holds the coordinated
bootstrap builder; existing feed payloads and keys are pinned and preserved.
