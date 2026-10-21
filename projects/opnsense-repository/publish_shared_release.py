#!/usr/bin/env python3
"""Replay a verified Hetzner/central release into the shared D4n13X hub.

Clone the latest hub first, prepare/sign against that inventory, and pass its
exact base commit. This publisher never builds packages, signs, deletes historical
artifacts, or changes Game Cache package bytes. Its existing catalog is updated as a
compatibility mirror of the combined shared catalog. Push is deliberately separate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

TRACK = 'FreeBSD:15:amd64/26.7'
PROJECT = 'projects/hetzner-firewall-updater'
CENTRAL = 'projects/opnsense-repository/'
FINGERPRINT = '994304f193330956c0892ba655068253821d0c5830e8bfc8cb252e2707d6e91c'
METADATA = {'meta', 'meta.conf', 'meta.pkg', 'meta.txz', 'data.pkg', 'data.txz',
            'packagesite.pkg', 'packagesite.txz', 'digests.txz'}
CENTRAL_FILES = {'build_bootstrap.py', 'install-repo.sh.in', 'bootstrap-build.json',
                 'GETTING_STARTED.md', 'publish_shared_release.py'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(root):
    record = json.loads((root/'repository-build.json').read_text())
    paths = {}
    for path in root.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Release refuses links/special files')
        if path.is_file(): paths[path.relative_to(root).as_posix()] = path
    if set(paths) != set(record['files']) | {'repository-build.json'}:
        raise ValueError('Unexpected release files')
    if len(paths) > 64 or sum(p.stat().st_size for p in paths.values()) > 64*1024*1024:
        raise ValueError('Release exceeds bounds')
    for name, expected in record['files'].items():
        if digest(paths[name]) != expected: raise ValueError('Release checksum mismatch')
    for name, expected in record['packages'].items():
        if digest(root/TRACK/name) != expected: raise ValueError('Package checksum mismatch')
    return record, paths


def package_map(record):
    result = {}
    for name, sha in record['packages'].items():
        match = re.fullmatch(r'(os-(?:gamecache|d4n13x-repo|hetzner-firewall-updater))-(\d+\.\d+\.\d+)\.pkg', name)
        if not match or match[1] in result: raise ValueError('Unexpected/duplicate package')
        result[match[1]] = (tuple(map(int, match[2].split('.'))), sha)
    return result


def stage(hub, release, legacy, expected_base):
    current = subprocess.check_output(['git', '-C', str(hub), 'rev-parse', 'HEAD'], text=True).strip()
    if current != expected_base: raise ValueError('Stale hub baseline; refresh and regenerate release')
    if subprocess.check_output(['git','-C',str(hub),'status','--porcelain'],text=True):
        raise ValueError('Publication checkout must start clean')
    old = json.loads((hub/'repository-build.json').read_text())
    new, files = checked(release)
    if new['public_key_der_sha256'] != FINGERPRINT or new['repository_url'] != old['repository_url']:
        raise ValueError('Unexpected shared trust or URL')
    if digest(release/'gamecache.pub') != digest(hub/'gamecache.pub'):
        raise ValueError('Existing D4n13X trust must be preserved')
    previous, incoming = package_map(old), package_map(new)
    if set(incoming) != {'os-gamecache','os-d4n13x-repo','os-hetzner-firewall-updater'}:
        raise ValueError('Combined catalog must contain all three packages')
    if incoming['os-gamecache'] != previous['os-gamecache']:
        raise ValueError('Hetzner publication must preserve exact Game Cache artifact')
    for name, (version, sha) in previous.items():
        if incoming[name][0] < version or incoming[name][0] == version and incoming[name][1] != sha:
            raise ValueError('Refusing version regression or changed published bytes')
    canonical_prefix = 'projects/gamecache/'
    for name in files:
        p = Path(name)
        canonical_relative = name[len(canonical_prefix):] if name.startswith(canonical_prefix) else ''
        canonical_path = Path(canonical_relative)
        allowed = (name in {'.nojekyll','gamecache.pub','repository-build.json','install-repo.sh'}
            or name.startswith(CENTRAL) and name[len(CENTRAL):] in CENTRAL_FILES
            or p.parent.as_posix() == TRACK and (p.name in METADATA or p.name in new['packages']
                or p.name in {'os-d4n13x-repo.pkg','os-d4n13x-repo.pkg.sha256'}))
        allowed = allowed or (name.startswith(canonical_prefix) and (canonical_relative in {'repository-build.json','central-bootstrap.json'} or canonical_path.parent.as_posix()==TRACK and (canonical_path.name in METADATA or canonical_path.name in new['packages'])))
        if not allowed: raise ValueError('Shared publication escaped allowlist: '+name)
    if canonical_prefix+'repository-build.json' in files:
        canonical = json.loads(files[canonical_prefix+'repository-build.json'].read_text())
        if canonical['packages'] != new['packages']:
            raise ValueError('Canonical combined catalog inventory differs')
        for name in new['packages']:
            if digest(release/canonical_prefix/TRACK/name) != new['packages'][name]:
                raise ValueError('Canonical package bytes differ')
        for name in METADATA:
            if (release/TRACK/name).exists() and digest(release/canonical_prefix/TRACK/name)!=digest(release/TRACK/name):
                raise ValueError('Canonical catalog metadata differs')
    compatibility, old_files = checked(legacy)
    if compatibility['packages'] != {n:s for n,s in new['packages'].items() if n.startswith('os-hetzner-firewall-updater-')}:
        raise ValueError('Compatibility feed must replay the identical updater')
    for name in old_files:
        p=Path(name)
        if not (name in {'.nojekyll','hetzner-firewall-updater.pub','HetznerFirewallUpdater.conf',
                'repository-build.json','GETTING_STARTED.md','install-repo.sh'}
                or p.parent.as_posix()==TRACK and (p.name in METADATA or p.name in compatibility['packages'])):
            raise ValueError('Compatibility publication escaped allowlist')
    if digest(legacy/'hetzner-firewall-updater.pub') != digest(hub/PROJECT/'hetzner-firewall-updater.pub'):
        raise ValueError('Preserve legacy signing trust')
    files = dict(files) | {PROJECT+'/'+n:p for n,p in old_files.items()}
    # Validate every destination before modifying any file.
    for name, source in files.items():
        target = hub/name
        if target.is_symlink() or any(p.is_symlink() for p in target.parents):
            raise ValueError('Destination refuses links')
        if target.exists() and re.fullmatch(r'os-.+-\d.*\.pkg',target.name) and digest(target)!=digest(source):
            raise ValueError('Immutable package already published with different bytes')
    for name, source in files.items():
        target=hub/name; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target); target.chmod(0o644)
    subprocess.run(['git','-C',str(hub),'add','--']+sorted(files),check=True)
    changed=subprocess.check_output(['git','-C',str(hub),'diff','--cached','--name-only'],text=True).splitlines()
    if not set(changed)<=set(files): raise ValueError('Unexpected staged paths')
    print('Validated and staged',len(changed),'files against base',expected_base)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hub',type=Path,required=True)
    parser.add_argument('--release',type=Path,required=True)
    parser.add_argument('--legacy',type=Path,required=True)
    parser.add_argument('--expected-base',required=True)
    args=parser.parse_args()
    stage(args.hub,args.release,args.legacy,args.expected_base)


if __name__=='__main__': main()
