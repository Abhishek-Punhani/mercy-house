"""Publish a sanitized local release to this project's dedicated Terraform VM.

Provider credentials are loaded by deploy/terraform.sh. The public app stores
provider settings only; team API keys are not deployed or embedded in Terraform.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess
import tarfile
import time
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'.deployment'


def envfile(path):
    result={}
    for line in Path(path).read_text().splitlines():
        line=line.strip().removeprefix('export ')
        if not line or line.startswith('#') or '=' not in line:continue
        key,value=line.split('=',1)
        result[key.strip()]=' '.join(shlex.split(value,comments=True))
    return result


def private_write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.touch(mode=0o600);path.chmod(0o600);path.write_text(value)


def tfoutputs():
    data=json.loads(subprocess.check_output([str(ROOT/'deploy/terraform.sh'),'output','-json'],cwd=ROOT))
    return {key:value['value'] for key,value in data.items()}


def ssh_args(host,login):
    return ['ssh','-i',str(Path.home()/'.ssh/google_compute_engine'),
      '-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=10',
      '-o','StrictHostKeyChecking=accept-new','-o','UserKnownHostsFile='+str(PRIVATE/'known_hosts'),login+'@'+host]


def command(host,login,text,**kwargs):
    return subprocess.run(ssh_args(host,login)+[text],check=True,**kwargs)


def upload(host,login,source,destination):
    options=ssh_args(host,login)[1:-1]
    subprocess.run(['scp',*options,str(source),login+'@'+host+':'+destination],check=True,stdout=subprocess.DEVNULL)


def wait_boot(host,login):
    deadline=time.monotonic()+600
    while time.monotonic()<deadline:
        result=subprocess.run(ssh_args(host,login)+['test -f /var/lib/mercy-house/bootstrap-ready'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if result.returncode==0:return
        time.sleep(5)
    raise RuntimeError('VM bootstrap did not become ready within ten minutes; inspect /var/log/mercy-bootstrap.log over SSH')


def render_release():
    if 'MERCY_PUBLIC_ORIGIN' not in (ROOT/'mercy/viewer/server.py').read_text():
        raise RuntimeError('Secure public-origin server contract is not present yet')
    allowed=['mercy','viewer','inputs','models','docker-compose.yml','Dockerfile.world',
      'Dockerfile.detective','Dockerfile.gateway','Dockerfile.workspace','.dockerignore']
    archive=PRIVATE/'release.tar.gz';manifest={}
    with tarfile.open(archive,'w:gz') as out:
        for name in allowed:
            path=ROOT/name
            files=sorted(path.rglob('*')) if path.is_dir() else [path]
            for f in files:
                if not f.is_file() or '__pycache__' in f.parts or f.suffix=='.pyc':continue
                relative=f.relative_to(ROOT);manifest[str(relative)]=hashlib.sha256(f.read_bytes()).hexdigest()
                out.add(f,arcname=str(relative),recursive=False)
    archive.chmod(0o600)
    record={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'files_sha256':manifest,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    private_write(PRIVATE/'source-manifest.json',json.dumps(record,indent=2)+'\n')
    return archive


def prepare_secrets(domain,reference):
    app=envfile(ROOT/'.env')
    # The public host stores no team API key. Each live run supplies its own
    # key for both detective and characters through the per-run gateway.
    clean={key:app[key] for key in ('MODEL','BASE_URL','APPEND_FILE') if key in app}
    if not clean.get('BASE_URL','').startswith('https://'):raise ValueError('Configure the public demo provider URL first')
    clean.update(MODE='full',TASK_ID='lantern_room',SEED='7',LOCAL_UID='1100',MERCY_PUBLIC_ORIGIN='https://'+domain,MERCY_PUBLIC_DEMO='1')
    if any(any(c in value for c in '\r\n\x00') for value in clean.values()):raise ValueError('Control character in app environment')
    private_write(PRIVATE/'app.env','\n'.join(key+'='+shlex.quote(value) for key,value in clean.items())+'\n')
    ref=envfile(reference);email=ref.get('TF_VAR_admin_email','admin@abhi07.xyz')
    if not re.fullmatch(r'[A-Za-z0-9._+@-]+',email):raise ValueError('Invalid ACME email')
    caddy=(ROOT/'deploy/Caddyfile.template').read_text().replace('__DOMAIN__',domain).replace('__ADMIN_EMAIL__',email)
    private_write(PRIVATE/'Caddyfile',caddy)
    return None


def checks(domain,login=None):
    base='https://'+domain
    def request(path='/',headers=None,data=None):
        req=urllib.request.Request(base+path,headers=headers or {},data=data)
        with urllib.request.urlopen(req,timeout=30) as response:return response.status,response.read(),response.headers
    status,html,_=request();assert status==200
    csrf=re.search(rb'name="mercy-csrf" content="([^"]+)"',html)[1].decode()
    _,raw,_=request('/api/config');config=json.loads(raw)
    _,raw,_=request('/api/runs');runs=json.loads(raw)['runs']
    assert len(config['tasks'])==8 and runs and config['public_demo'] and not config['key_configured']
    for path in ('/.env','/logs/private/world.json','/terraform/terraform.tfstate'):
        try:request(path);raise AssertionError('Private path was exposed')
        except urllib.error.HTTPError as exc:assert exc.code==404,(path,exc.code)
    bad={'Origin':'https://other.invalid','X-Mercy-CSRF':csrf,'Content-Type':'application/json'}
    try:request('/api/runs',bad,b'{}');raise AssertionError('Wrong origin was accepted')
    except urllib.error.HTTPError as exc:assert exc.code==403,exc.code
    probe={'Origin':base,'X-Mercy-CSRF':csrf,'Content-Type':'application/json'}
    for payload in ({'use_configured_key':True},{'api_key':''},{'base_url':'https://other.invalid','api_key':'not-a-key'}):
        try:request('/api/runs',probe,json.dumps(payload).encode());raise AssertionError('Public key/provider requirement bypassed')
        except urllib.error.HTTPError as exc:assert exc.code==400,exc.code
    _,raw,_=request('/api/runs');assert len(json.loads(raw)['runs'])==len(runs)
    ident=runs[0]['id'];_,wire,h=request('/api/runs/'+ident+'/events')
    assert 'text/event-stream' in h['Content-Type'] and b'opening' in wire
    return {'https_certificate':'verified by system trust store','anonymous_ui_config_and_replays':'200; no login',
       'private_paths':'404','wrong_origin':'403','server_key_access':'denied',
       'public_live_runs':'visitor key for detective and characters; configured provider only',
       'invalid_key_or_provider_creates_no_run':'400','sse_replay':'passed','tasks':len(config['tasks']),
       'replays':len(runs),'key_configured':config['key_configured'],'public_demo':True,'generation_calls':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-env',type=Path,default=Path('/home/manav/dev_ws/N8N-Agent /terraform/.env'))
    parser.add_argument('--checks-only',action='store_true')
    args=parser.parse_args();PRIVATE.mkdir(exist_ok=True);PRIVATE.chmod(0o700)
    outputs=tfoutputs();host=outputs['instance_ip'];domain=outputs['domain_name'];login_name='manav'
    if args.checks_only:login=None
    else:
        archive=render_release();login=prepare_secrets(domain,args.reference_env);wait_boot(host,login_name)
        # No active production investigation may be interrupted by a release.
        check="python3 -c \"import urllib.request,json; d=json.load(urllib.request.urlopen('http://localhost:8787/api/runs',timeout=2)); assert not any(r['status'] in ('starting','building','running','stopping') for r in d['runs'])\""
        result=subprocess.run(ssh_args(host,login_name)+[check],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        # A missing listener is expected for first installation. Verify active
        # service only when systemd says it is already running.
        active=subprocess.run(ssh_args(host,login_name)+['systemctl is-active --quiet mercy-house'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if active.returncode==0 and result.returncode!=0:raise RuntimeError('Production viewer is active or unreadable; finish its investigation before redeploy')
        remote='/tmp/mercy-release-'+secrets.token_hex(5)
        command(host,login_name,'umask 077; mkdir '+shlex.quote(remote),stdout=subprocess.DEVNULL)
        for file in [archive,PRIVATE/'app.env',PRIVATE/'Caddyfile',PRIVATE/'source-manifest.json',ROOT/'deploy/mercy-house.service']:
            upload(host,login_name,file,remote+'/'+file.name)
        remote_script='''set -euo pipefail
sudo systemctl stop mercy-house 2>/dev/null || true
sudo tar -xzf "$1/release.tar.gz" -C /opt/mercy-house --no-same-owner
sudo chown -R mercyhouse:mercyhouse /opt/mercy-house
sudo install -o mercyhouse -g mercyhouse -m600 "$1/app.env" /opt/mercy-house/.env
sudo install -o mercyhouse -g mercyhouse -m600 "$1/source-manifest.json" /opt/mercy-house/deployment-source-manifest.json
sudo install -m644 "$1/mercy-house.service" /etc/systemd/system/mercy-house.service
sudo install -o root -g caddy -m640 "$1/Caddyfile" /etc/caddy/Caddyfile
sudo -u mercyhouse mkdir -p /opt/mercy-house/logs/public /opt/mercy-house/logs/private
sudo chmod 700 /opt/mercy-house/logs /opt/mercy-house/logs/public /opt/mercy-house/logs/private
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl daemon-reload
sudo systemctl enable --now mercy-house
sudo systemctl enable --now caddy
sudo systemctl reload caddy
rm -rf "$1"
'''
        command(host,login_name,'bash -s -- '+shlex.quote(remote),input=remote_script.encode(),stdout=subprocess.DEVNULL)
    deadline=time.monotonic()+360
    while True:
        try:result=checks(domain,login);break
        except (OSError,AssertionError) as exc:
            if time.monotonic()>deadline:raise
            time.sleep(5)
    result.update(url='https://'+domain,instance_name=outputs['instance_name'],instance_ip=host,
        credential_file=str(PRIVATE/'access.json'),source_manifest=str(PRIVATE/'source-manifest.json'))
    private_write(PRIVATE/'verification.json',json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='credential_file'}))


if __name__=='__main__':main()
