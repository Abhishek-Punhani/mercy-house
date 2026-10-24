"""SSH to the Terraform VM, pull main there, rebuild runtimes and restart the viewer.

Unlike docker compose up, rebuilding the investigation images does not launch a
paid detective episode. The long-running web viewer is a systemd service.
"""
import json
from pathlib import Path
import subprocess
import time

from publish import PRIVATE, ROOT, checks, command, private_write, tfoutputs

REMOTE_SCRIPT = r'''set -euo pipefail
APP=/opt/mercy-house
REPO=https://github.com/Abhishek-Punhani/mercy-house.git
stage=''
stopped=0
cleanup() {
  code=$?
  if [ "$stopped" = 1 ]; then sudo systemctl start mercy-house || true; fi
  if [ -n "$stage" ]; then sudo -u mercyhouse rm -rf -- "$stage"; fi
  exit "$code"
}
trap cleanup EXIT
if ! command -v git >/dev/null; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git
fi
# Preserve an existing investigation rather than terminating its containers.
if systemctl is-active --quiet mercy-house; then
  sudo -u mercyhouse python3 - <<'GUARD'
import json,urllib.request
runs=json.load(urllib.request.urlopen('http://localhost:8787/api/runs',timeout=5))['runs']
assert not any(r['status'] in ('starting','building','running','stopping') for r in runs), 'An investigation is active; retry after it finishes'
GUARD
fi
if ! sudo -u mercyhouse test -d "$APP/.git"; then
  # Adopt the original archive installation only if its recorded runtime files
  # are unchanged. Credentials, logs and Terraform state are never replaced.
  sudo -u mercyhouse python3 - <<'ADOPT'
from pathlib import Path
import hashlib,json
root=Path('/opt/mercy-house')
m=json.loads((root/'deployment-source-manifest.json').read_text())
bad=[n for n,h in m['files_sha256'].items() if not (root/n).is_file() or hashlib.sha256((root/n).read_bytes()).hexdigest()!=h]
assert not bad, 'Remote runtime files have edits; refusing to replace: '+', '.join(bad)
ADOPT
  stage=$(sudo -u mercyhouse mktemp -d /opt/mercy-house/.git-adopt.XXXXXX)
  sudo -u mercyhouse git clone --no-checkout --branch main "$REPO" "$stage/repo"
else
  origin=$(sudo -u mercyhouse git -C "$APP" remote get-url origin)
  if [ "$origin" != "$REPO" ]; then echo 'Unexpected remote origin; refusing update' >&2; exit 1; fi
  sudo -u mercyhouse git -C "$APP" diff --exit-code --quiet
  sudo -u mercyhouse git -C "$APP" diff --cached --exit-code --quiet
fi
# Stop the launcher before changing files, so no new case can start mid-update.
sudo systemctl stop mercy-house
stopped=1
if [ -n "$stage" ]; then
  sudo -u mercyhouse mv "$stage/repo/.git" "$APP/.git"
  sudo -u mercyhouse git -C "$APP" reset --mixed --quiet HEAD
  sudo -u mercyhouse git -C "$APP" restore --source=HEAD --worktree -- .
fi
branch=$(sudo -u mercyhouse git -C "$APP" branch --show-current)
if [ "$branch" != main ]; then echo 'Remote checkout must be on main' >&2; exit 1; fi
printf 'Pulling GitHub main on the GCP VM...\n'
sudo -u mercyhouse git -C "$APP" pull --ff-only origin main
printf 'Rebuilding all four investigation images...\n'
sudo -u mercyhouse docker compose --project-directory "$APP" -f "$APP/docker-compose.yml" build
sudo -u mercyhouse python3 - <<'MANIFEST'
from pathlib import Path
import hashlib,json,subprocess
root=Path('/opt/mercy-house')
names=subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split('\0')
allowed={'mercy','viewer','inputs','models','docker-compose.yml','Dockerfile.world','Dockerfile.detective','Dockerfile.gateway','Dockerfile.workspace','.dockerignore'}
files={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names if n and n.split('/')[0] in allowed and (root/n).is_file()}
record={'commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'method':'remote git pull --ff-only origin main; docker compose build; systemd viewer restart','files_sha256':files}
p=root/'deployment-source-manifest.json';p.write_text(json.dumps(record,indent=2)+'\n');p.chmod(0o600)
print(json.dumps({'deployed_commit':record['commit'],'runtime_files':len(files)}))
MANIFEST
sudo systemctl start mercy-house
stopped=0
sudo systemctl is-active --quiet mercy-house
printf 'Git pull, Docker rebuild and viewer restart complete.\n'
'''


def main():
    PRIVATE.mkdir(exist_ok=True)
    PRIVATE.chmod(0o700)
    outputs = tfoutputs()
    command(outputs['instance_ip'], 'manav', 'bash -s', input=REMOTE_SCRIPT.encode())
    deadline = time.monotonic() + 120
    while True:
        try:
            result = checks(outputs['domain_name'])
            break
        except (OSError, AssertionError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(3)
    result.update(url='https://' + outputs['domain_name'], method='remote Git pull and Docker build; systemd restart')
    private_write(PRIVATE/'git-redeploy-verification.json', json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
