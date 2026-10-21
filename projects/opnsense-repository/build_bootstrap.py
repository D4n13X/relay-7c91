#!/usr/bin/env python3
"""Build the shared os-d4n13x-repo on FreeBSD, preserving existing feed trust.

Public inputs only; no signing keys are read by this package builder.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile

VERSION='0.4.5'
BASELINE_SHA256='c4d15b313542feb55ef12e6535de7596fc405167d976439dc4bd088e054637a0'
GAMECACHE_DER='994304f193330956c0892ba655068253821d0c5830e8bfc8cb252e2707d6e91c'
BASE='https://d4n13x.github.io/relay-7c91'
TRACK='FreeBSD:15:amd64/26.7'


def command(args):
    return subprocess.run(args,check=True,capture_output=True,timeout=90).stdout


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if platform.system()!='FreeBSD' or command(['pkg','config','ABI']).decode().strip()!='FreeBSD:15:amd64':
        raise SystemExit('Requires matching native FreeBSD 15 amd64 pkg')
    if hashlib.sha256(args.baseline.read_bytes()).hexdigest()!=BASELINE_SHA256:
        raise SystemExit('Baseline bootstrap does not match preserved public release')
    old=json.loads(command(['tar','-xOf',str(args.baseline),'+MANIFEST']))
    if old['name']!='os-d4n13x-repo': raise SystemExit('Wrong central baseline identity')
    payload={}
    for name in ('etc/pkg/repos/GameCache.conf','etc/pkg/keys/gamecache.pub'):
        payload[name]=command(['tar','-xOf',str(args.baseline),'/usr/local/'+name])
    old_config=json.loads(payload['etc/pkg/repos/GameCache.conf'])
    expected={'D4n13X':{'url':BASE+'/projects/gamecache/'+TRACK,'enabled':True,'signature_type':'pubkey',
                       'pubkey':'/usr/local/etc/pkg/keys/gamecache.pub','priority':10}}
    if old_config!=expected: raise SystemExit('Unexpected baseline repository configuration')
    product=dict(product_abi='26.7',product_arch='amd64',product_id='os-d4n13x-repo',
        product_name='d4n13x-repo',product_version=VERSION,product_tier='3',product_email='D4n13X',
        product_website='https://github.com/D4n13X/relay-7c91')
    payload['opnsense/version/d4n13x-repo']=json.dumps(product,indent=2).encode()+b'\n'
    args.output.mkdir(parents=True,exist_ok=True)
    target=args.output/('os-d4n13x-repo-'+VERSION+'.pkg')
    if target.exists(): raise SystemExit('Refusing to rebuild an existing versioned artifact')
    with tempfile.TemporaryDirectory(prefix='d4n13x-central-bootstrap-') as temporary:
        stage=Path(temporary)
        for name,data in payload.items():
            path=stage/'usr/local'/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data);path.chmod(0o644)
        for filename,fingerprint in [('gamecache.pub',GAMECACHE_DER)]:
            der=command(['openssl','pkey','-pubin','-in',str(stage/'usr/local/etc/pkg/keys'/filename),'-outform','DER'])
            if hashlib.sha256(der).hexdigest()!=fingerprint: raise SystemExit('Unexpected feed signing trust')
        manifest=dict(name='os-d4n13x-repo',version=VERSION,origin='opnsense/os-d4n13x-repo',
            comment='D4n13X shared plugin repository',maintainer='D4n13X',www=BASE,prefix='/usr/local',
            desc='One D4n13X signed repository for all D4n13X OPNsense plugins.',
            abi='FreeBSD:15:amd64',arch='freebsd:15:amd64',licenselogic='single',licenses=['BSD2CLAUSE'],
            annotations=product,
            scripts={'post-install':'/usr/local/opnsense/scripts/firmware/register.php install os-d4n13x-repo',
                     'post-deinstall':'/usr/local/opnsense/scripts/firmware/register.php remove os-d4n13x-repo'})
        (stage/'manifest.json').write_text(json.dumps(manifest))
        (stage/'plist').write_text(''.join('/usr/local/'+name+'\n' for name in payload))
        command(['pkg','create','-M',str(stage/'manifest.json'),'-r',str(stage),'-p',str(stage/'plist'),'-o',str(args.output)])
    receipt={'name':'os-d4n13x-repo','version':VERSION,'artifact':target.name,
        'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'baseline_sha256':BASELINE_SHA256,
        'files':{name:hashlib.sha256(data).hexdigest() for name,data in payload.items()},
        'feed_public_key_der_sha256':{'D4n13X':GAMECACHE_DER}}
    (args.output/'bootstrap-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__': main()
