# Hetzner Firewall Updater — beta getting started

Keep one existing Hetzner Robot firewall rule in sync with your OPNsense WAN
IPv4. Each team member installs the plugin on their own OPNsense and selects
their own uniquely named incoming rule on the shared dedicated server.
No coordinator, external IP service or permanent daemon is needed.

## Before you install

- Use **OPNsense 26.7 amd64**. The installation and UI were tested on **26.7.7 /
  FreeBSD 15.1-RELEASE-p4**. Other releases and architectures are not qualified.
- Export an OPNsense configuration backup and store it privately.
- Have a Hetzner **Robot webservice** username/password and numeric dedicated
  server ID. Hetzner Cloud API tokens do not work.
- In Robot, prepare exactly one **incoming** rule with your assigned exact name,
  explicitly set to **IPv4**, with the intended action, protocol and ports.
  The plugin changes only its source IP and never creates rules.
- The selected OPNsense interface needs exactly one non-alias **public IPv4**.
  Private/CGNAT addresses and a WAN behind NAT are unsupported. Both incoming
  and outgoing firewall rule lists must be nonempty; only the main switch port
  is supported.

**Beta scope:** native build, install/upgrade, package integrity, firmware
registration, UI and disabled saves are verified. Live Robot writes, enabled
interface-event/cron behavior and reboot/removal have not yet been qualified.
Use a test server/firewall first and retain independent management access.

## 1. Add the signed package source

Open an OPNsense **root shell** (console option 8 or SSH) and run:

```sh
fetch -qo - https://d4n13x.github.io/relay-7c91/projects/hetzner-firewall-updater/install-repo.sh | sh
```

This installs the **repository package for ongoing updates**, verifies its pinned
checksum and signing key, and authenticates a fresh signed catalog. It does not
install or enable the plugin. Re-running it checks the existing repository
package and refreshes the catalog without downgrading a newer installer.

Existing D4n13X/Game Cache sources stay intact. Users who already installed
`os-d4n13x-repo` still need this Hetzner-specific setup once. The script is
[available to inspect](https://github.com/D4n13X/relay-7c91/blob/main/projects/hetzner-firewall-updater/install-repo.sh).

Independent signing-key fingerprint (public DER SHA-256):

```text
71540faf358ef598ec86ec0b0e4a9e804b8a0bf80406509faf30f55bec8ecdfa
```

## 2. Install the plugin

In the root shell:

```sh
pkg install -r HetznerFirewallUpdater os-hetzner-firewall-updater
pkg check -s os-hetzner-firewall-updater os-hetzner-firewall-updater-repo
```

Review the proposed transaction. Python 3.13 may be installed if absent, using
the matching OPNsense repository. Do not force incompatible dependencies.
Refresh the browser, then open **Services → Hetzner Firewall Updater**.
Installation starts **disabled** and makes no Hetzner changes.

## 3. Configure and test

1. Open **Settings**. Keep **Enabled** unchecked for the first test.
2. Enter the Robot webservice username/password and numeric **Server ID**.
3. Enter your assigned **Rule Name** exactly, including case. Every tester must
   have a different rule name; missing or duplicate names are rejected.
4. Select your logical **Network Interface**, usually **WAN**. Leave the
   **Check Interval** at **5 minutes** initially.
5. Click **Save**, switch to **Status**, and click **Test Connection**. This
   checks credentials, server access and rule existence without modifying Robot.
6. Check the displayed local IPv4. Click **Sync Now** for your first deliberate
   remote update. This button can update the rule even while automatic checks
   are disabled. Verify the rule's source IP directly in Robot and confirm the
   other rules and firewall settings remain as intended.
7. Return to Settings, check **Enabled**, and **Save** to turn on automatic
   interface-change and periodic checks.

Credential fields stay blank after loading; blank means **keep the stored
value**. Enter replacements to rotate credentials. Robot credentials may grant
much broader access than your assigned rule: the plugin's restriction is a
client-side safeguard. OPNsense configuration exports/backups contain the stored
credentials; protect them.

## 4. Understand status and ongoing operation

Status shows the selected interface, current local IPv4, last observed Robot
source, synchronization attempt/success times, and any error. Remote values
are observations from the last remote check. Refreshing the page never writes
the firewall or contacts Robot.

Repeated interface events are debounced. Checks include randomized jitter;
unchanged local addresses normally skip API calls, with occasional remote drift
reconciliation. Temporary outages/conflicts retry within bounds and recover on
later scheduled checks. No permanent worker runs.

Robot requires submitting a complete ruleset and has no atomic conditional
update. Independent testers can race and overwrite each other's changes despite
fresh reads, verification, jitter and retries. Periodic reconciliation reduces
drift but cannot guarantee that no race occurs.

## Updates and removal

Once the source is installed, future versions are obtained through the signed
catalog. Refresh the native plugin list, or use:

```sh
pkg update -r HetznerFirewallUpdater
pkg upgrade -n -r HetznerFirewallUpdater os-hetzner-firewall-updater
pkg upgrade -r HetznerFirewallUpdater os-hetzner-firewall-updater
```

Disable the plugin and save before removal. Wait for any running operation to
finish, then remove only these two packages if desired:

```sh
pkg delete os-hetzner-firewall-updater os-hetzner-firewall-updater-repo
```

Saved plugin settings/history are retained; configuration backups may still
contain credentials. Removing the repository package removes only its own
source/key and registration. Game Cache and normal OPNsense repositories remain.

## If something fails

- **Public IPv4 required:** choose the actual public-address interface. There is
  no external IP fallback for NAT/CGNAT.
- **Rule missing/duplicate/IPv4 required:** correct the exact incoming rule in
  Robot; do not rename another tester's rule.
- **Authentication/access failure:** use Robot webservice credentials and verify
  the server ID. Avoid repeatedly testing bad credentials.
- **Processing/busy/outage:** wait for the next check; bounded retries and local
  locking prevent overlapping jobs.
- **Unrelated settings changed during verification:** inspect Robot for other
  clients' changes; the plugin will not restore a stale snapshot.

Report the plugin/OPNsense versions, displayed error, interface type (DHCP/PPPoE/
static), whether Test Connection passes, and the expected/observed behavior.
**Never send passwords, API credentials, config.xml or configuration backups.**
