#!/usr/bin/env python3
"""Coordinated central release: migrate only Game Cache's URL; preserve both trusts.

This source is published canonically under projects/opnsense-repository/. It is
not invoked by Game Cache package builds or ordinary Game Cache publications.
All inputs are public; private signing keys remain on the workstation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile

VERSION = '0.4.4'
BASELINE_VERSION = '0.4.3'
BASELINE_SHA256 = 'e2bc0ce276d41959a5cfde7dd11230d3ad2388fdb92a18b189a66a46dfa646e8'
GAMECACHE_DER = '994304f193330956c0892ba655068253821d0c5830e8bfc8cb252e2707d6e91c'
HETZNER_DER = '71540faf358ef598ec86ec0b0e4a9e804b8a0bf80406509faf30f55bec8ecdfa'
BASE = 'https://d4n13x.github.io/relay-7c91'
TRACK = 'FreeBSD:15:amd64/26.7'
PAYLOAD = ('etc/pkg/repos/GameCache.conf', 'etc/pkg/keys/gamecache.pub',
           'etc/pkg/repos/HetznerFirewallUpdater.conf', 'etc/pkg/keys/hetzner-firewall-updater.pub',
           'opnsense/version/d4n13x-repo')


def command(args):
    return subprocess.run(args, check=True, capture_output=True, timeout=90).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--baseline-receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if platform.system() != 'FreeBSD' or command(['pkg', 'config', 'ABI']).decode().strip() != 'FreeBSD:15:amd64':
        raise SystemExit('Requires matching native FreeBSD 15 amd64 pkg')
    baseline = json.loads(args.baseline_receipt.read_text())
    if (baseline['version'] != BASELINE_VERSION or baseline['sha256'] != BASELINE_SHA256
            or hashlib.sha256(args.baseline.read_bytes()).hexdigest() != BASELINE_SHA256):
        raise SystemExit('Baseline does not match the current coordinated central release')
    old = json.loads(command(['tar', '-xOf', str(args.baseline), '+MANIFEST']))
    if old['name'] != 'os-d4n13x-repo' or old['version'] != BASELINE_VERSION:
        raise SystemExit('Unexpected baseline package identity')
    payload = {name: command(['tar', '-xOf', str(args.baseline), '/usr/local/' + name]) for name in PAYLOAD}
    if {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()} != baseline['files']:
        raise SystemExit('Baseline owned files differ from the preserved central receipt')
    configuration = json.loads(payload['etc/pkg/repos/GameCache.conf'])
    expected = {'D4n13X': {'url': BASE + '/' + TRACK, 'enabled': True, 'signature_type': 'pubkey',
                          'pubkey': '/usr/local/etc/pkg/keys/gamecache.pub', 'priority': 10}}
    if configuration != expected:
        raise SystemExit('Unexpected baseline Game Cache URL or policy; coordinate a new migration')
    # A byte replacement preserves every other setting and original formatting.
    payload['etc/pkg/repos/GameCache.conf'] = payload['etc/pkg/repos/GameCache.conf'].replace(
        (BASE + '/' + TRACK).encode(), (BASE + '/projects/gamecache/' + TRACK).encode())
    product = json.loads(payload['opnsense/version/d4n13x-repo'])
    product['product_version'] = VERSION
    payload['opnsense/version/d4n13x-repo'] = json.dumps(product, indent=2).encode() + b'\n'
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / ('os-d4n13x-repo-' + VERSION + '.pkg')
    if target.exists():
        raise SystemExit('Refusing to rebuild an existing central versioned artifact')
    with tempfile.TemporaryDirectory(prefix='d4n13x-central-migration-') as temporary:
        stage = Path(temporary)
        for name, data in payload.items():
            path = stage / 'usr/local' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o644)
        for filename, fingerprint in [('gamecache.pub', GAMECACHE_DER), ('hetzner-firewall-updater.pub', HETZNER_DER)]:
            der = command(['openssl', 'pkey', '-pubin', '-in', str(stage / 'usr/local/etc/pkg/keys' / filename), '-outform', 'DER'])
            if hashlib.sha256(der).hexdigest() != fingerprint:
                raise SystemExit('Unexpected feed signing trust')
        fields = ('name', 'origin', 'comment', 'maintainer', 'www', 'prefix', 'desc', 'abi', 'arch', 'licenselogic', 'licenses', 'scripts')
        manifest = {name: old[name] for name in fields}
        manifest.update(version=VERSION, annotations=product)
        (stage / 'manifest.json').write_text(json.dumps(manifest))
        (stage / 'plist').write_text(''.join('/usr/local/' + name + '\n' for name in payload))
        command(['pkg', 'create', '-M', str(stage / 'manifest.json'), '-r', str(stage),
                 '-p', str(stage / 'plist'), '-o', str(args.output)])
    receipt = {'name': 'os-d4n13x-repo', 'version': VERSION, 'artifact': target.name,
               'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'baseline_sha256': BASELINE_SHA256,
               'files': {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()},
               'feed_public_key_der_sha256': {'D4n13X': GAMECACHE_DER, 'HetznerFirewallUpdater': HETZNER_DER}}
    (args.output / 'bootstrap-build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
