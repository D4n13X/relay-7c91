# Game Cache beta: getting started

Cache Steam downloads on your OPNsense appliance using a dedicated disk.
This is an experimental beta for **OPNsense 26.7 amd64, FreeBSD 15.1 and Unbound**.
Use a test appliance and save an OPNsense configuration backup first.

**Available:** Steam caching, basic statistics and service status.
**Still planned:** Battle.net support, dashboard charts, richer statistics, and
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

The repository installer always has the same download URL; its internal version
advances with releases. Run this in a root **`/bin/sh`** shell:

```sh
set -eu
feed='https://d4n13x.github.io/relay-7c91/FreeBSD:15:amd64/26.7'
fetch -o /tmp/os-d4n13x-repo.pkg "$feed/os-d4n13x-repo.pkg"
fetch -o /tmp/os-d4n13x-repo.pkg.sha256 "$feed/os-d4n13x-repo.pkg.sha256"
test "$(sha256 -q /tmp/os-d4n13x-repo.pkg)" = "$(cat /tmp/os-d4n13x-repo.pkg.sha256)"
pkg add -M /tmp/os-d4n13x-repo.pkg
pkg update -r D4n13X
pkg install -r D4n13X os-gamecache
```

Stop if any command fails. If the checksum comparison fails during a release,
download both files again. The checksum checks the download; the initial
repository installer is trusted through HTTPS. Subsequent feed updates use its
public signing key. Review the package transaction before accepting it.

If `os-d4n13x-repo` is already installed, skip the download/add steps and use:

```sh
pkg update -r D4n13X
pkg install -r D4n13X os-d4n13x-repo os-gamecache
```

The older `os-gamecache-repo` name requires a one-time migration; ask the beta
coordinator instead of installing a second bootstrap over it.

## 3. Configure Services → Game Cache

1. Refresh the web interface after installation, then open **Services → Game Cache**.
2. Enter your mounted storage's device path, partition UUID and mountpoint.
   Set cache capacity, free-space reserve and key-zone budget for your disk/RAM.
3. Select the static interface and reserved cache IPv4 address. Enter allowed
   client networks and independent public upstream DNS servers. Do not create
   an additional persistent VIP for the same address.
4. Save and validate the settings. Enable caching and Steam discovery DNS, then
   save and apply. Wait for healthy service status before testing.
5. Make sure test clients use this appliance's Unbound resolver for DNS.

Fresh installations start disabled. Installing the package alone does not turn
on caching or change client DNS. HTTPS traffic passes through without decryption;
it is not counted as cached content.

## 4. Test Steam and send feedback

Download a small Steam game, uninstall it on the test client, and download the
same content again. Cached HTTP requests should show HIT activity on the second
download. Content changes and uncached traffic can still need internet access.
Current statistics are a bounded log sample; they are not an exact WAN-savings
meter. Dashboard charts are not available in this beta yet.

Send the beta coordinator your OPNsense/plugin versions, game, test time, service
status and the before/after statistics. Include any error message. Review logs
before sharing them; remove credentials, private addresses and personal data.

## Update or stop

Use the two update commands in step 2 for later betas and review the transaction.
To stop caching, use **Stop**. To keep it disabled after a reboot, disable the
plugin and apply. Cache data is retained.

To remove the plugin, run `pkg delete os-gamecache`; settings and cache data remain.
Keep `os-d4n13x-repo` if you want updates for other D4n13X projects.
