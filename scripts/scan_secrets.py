"""Scan tracked files and reachable Git blobs without printing secret values."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def credentials():
    values=set()
    for file in (ROOT/'.env',ROOT/'terraform/.env'):
        if not file.exists():continue
        for line in file.read_text().splitlines():
            if '=' not in line or line.lstrip().startswith('#'):continue
            key,value=line.removeprefix('export ').split('=',1)
            if any(token in key.upper() for token in ('API_KEY','API_TOKEN','PASSWORD','SECRET')):
                value=value.strip().strip('\"\'')
                if len(value)>=12:values.add(value.encode())
    return values


def main():
    known=credentials();findings=[]
    private=re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC |DSA |ENCRYPTED )?PRIVATE KEY-----')
    token=re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,})\b')
    def check(data,label):
        if any(value in data for value in known):findings.append({'path':label,'kind':'configured credential'})
        if private.search(data):findings.append({'path':label,'kind':'private key material'})
        if token.search(data):findings.append({'path':label,'kind':'API token pattern'})
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    denied=[]
    for name in filter(None,tracked):
        p=Path(name)
        if p.name=='.env' or '.deployment' in p.parts or '.terraform' in p.parts or '.ssh' in p.parts or '.tfstate' in p.name or p.suffix in ('.pem','.key','.p12','.pfx','.tfplan'):
            denied.append(name)
        path=ROOT/p
        if path.is_file():check(path.read_bytes(),name)
    listing=subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT).decode().splitlines()
    objects=[];seen=set()
    for line in listing:
        oid,_,name=line.partition(' ')
        if oid not in seen:objects.append((oid,name or oid));seen.add(oid)
    proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    blobs=0
    try:
        for oid,name in objects:
            proc.stdin.write((oid+'\n').encode());proc.stdin.flush()
            header=proc.stdout.readline().decode().split();size=int(header[2]);data=proc.stdout.read(size);proc.stdout.read(1)
            if header[1]=='blob':blobs+=1;check(data,'history:'+name)
    finally:
        proc.stdin.close();proc.stdout.close();proc.wait()
    result={'passed':not findings and not denied,'tracked_paths':len(list(filter(None,tracked))),'reachable_history_blobs':blobs,
            'configured_credentials_checked':len(known),'forbidden_tracked_paths':denied,'findings':findings,
            'scope':'Known configured task credentials, GitHub/API token patterns and private-key headers in tracked files and all reachable Git blobs. No secret values printed. Masked video form visually reviewed separately.'}
    (ROOT/'docs/SECURITY_SCAN.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));return 0 if result['passed'] else 1


if __name__=='__main__':sys.exit(main())
