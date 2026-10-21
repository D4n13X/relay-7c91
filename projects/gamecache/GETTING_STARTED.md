# Game Cache beta: getting started

Cache Steam downloads on your OPNsense appliance using a dedicated disk.
This is an experimental beta for **OPNsense 26.7 amd64, FreeBSD 15.1 and Unbound**.
Use a test appliance and save an OPNsense configuration backup first.

**Available in 0.4.1:** Steam caching, traffic and HIT/MISS charts, service status,
and a native Game Cache dashboard widget.
**Still planned:** Battle.net support, incremental retained statistics, and
disk selection/format/mount controls. Other listed platforms remain disabled.

## 1. Before you install

- Have root shell access and an existing Unbound DNS configuration.
- Prepare and mount a dedicated UFS filesystem on a separate physical disk.
  Have its stable device path (such as `/dev/gpt/gamecache`), partition UUID and
  mountpoint ready. The beta has no disk setup wizard; ask the beta coordinator
  for storage preparation if needed. Formatting erases a disk; never use the
  OPNsense system disk. Installation itself does not format anything.
- Reserve an unused IPv4 address on a static LAN/OPT interface, outside the DHCP
  allocation. Know the client subnet and independent public upstream DNS servers.
- Install `nginx` and `python313` from the matching OPNsense package repository
  if they are absent. Keep dependencies from OPNsense.

## 2. Add the D4n13X repository and install

Use the same shared installer for every D4n13X plugin. Run these commands as root
in the appliance shell (`tcsh` is supported; the installer runs through `sh`):

```sh
fetch -qo - https://d4n13x.github.io/relay-7c91/install-repo.sh | sh
pkg install -r D4n13X os-gamecache
```

The installer downloads the independently versioned **os-d4n13x-repo** package,
checks its pinned checksum and both public signing-key fingerprints, and verifies
fresh signed catalogs. It configures both Game Cache and Hetzner feeds without
enabling either plugin. Review the plugin package transaction before accepting it.
The initial installer is trusted through HTTPS; later catalogs are signed.

For later updates, run the same two commands. A current or newer central bootstrap
is kept rather than downgraded. The retired standalone Hetzner bootstrap is migrated
with a private rollback backup. If you still have the historical
`os-gamecache-repo` name, ask your beta coordinator about the one-time migration.

Game Cache's native repository identifier stays **D4n13X**. Its canonical feed is
under `projects/gamecache/`; the old root feed and old versioned downloads remain
available for clients that have not yet received the central URL update.

## 3. Configure Services → Game Cache

1. Refresh the web interface after installation, then open **Services → Game Cache**.
   Its pages are Overview, Settings, Storage, Platforms and Diagnostics.
2. On **Storage**, enter your mounted filesystem's device path, partition UUID
   and mountpoint. Set cache capacity, free-space reserve and key-zone budget,
   then save. Keep the service disabled until the network settings are ready.
3. On **Settings**, select the static interface and reserved cache IPv4 address.
   Add allowed client networks and independent public upstream DNS servers as
   separate entries. Do not create an additional persistent VIP for that address.
4. Enable caching and Steam discovery DNS on **Settings**, then Save and apply.
   Check **Overview** for healthy status; use **Diagnostics** to validate saved
   settings or inspect errors. **Platforms** shows Steam/Battle.net support states.
5. Make sure test clients use this appliance's Unbound resolver for DNS.

Fresh installations start disabled. Installing the package alone does not turn
on caching or change client DNS. HTTPS traffic passes through without decryption;
it is not counted as cached content.

## 4. Test Steam and send feedback

Download a small Steam game, uninstall it on the test client, and download the
same content again. Cached HTTP requests should show HIT activity on the second
download. Content changes and uncached traffic can still need internet access.
Current statistics are a bounded log sample; they are not an exact WAN-savings
meter.

Charts appear under **Services → Game Cache → Overview**.
Choose the last hour, 24 hours or seven days. To add the main dashboard widget,
open **Lobby → Dashboard**, use Edit/Add widget, select **Game Cache**, then Save.
Widgets are saved per user. The charts show the available log sample, which can
cover less than the selected window. Battle.net remains unqualified.

Send the beta coordinator your OPNsense/plugin versions, game, test time, service
status and the before/after statistics. Include any error message. Review logs
before sharing them; remove credentials, private addresses and personal data.

## Update or stop

Use the two update commands in step 2 for later betas and review the transaction.
To stop caching, use **Stop**. To keep it disabled after a reboot, disable the
plugin and apply. Cache data is retained.

To remove the plugin, run `pkg delete os-gamecache`; settings and cache data remain.
Keep `os-d4n13x-repo` if you want updates for other D4n13X projects.
