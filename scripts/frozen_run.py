"""Run a local experiment against a frozen source tree while development continues.

Credentials stay in inherited environment variables; they are never copied into
the frozen tree or manifest. This runner is trusted development tooling.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python scripts/frozen_run.py MODULE [ARGS...]')
    root = Path(__file__).resolve().parents[1]
    frozen = root / 'logs' / ('frozen-source-' + str(time.time_ns()))
    frozen.mkdir(parents=True)
    shutil.copytree(root / 'mercy', frozen / 'mercy', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(root / 'inputs', frozen / 'inputs')
    env = dict(os.environ)
    config = root / '.env'
    if config.exists():
        for line in config.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                env.setdefault(key.strip(), value.strip().strip('"'))
    manifest = {str(p.relative_to(frozen)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(frozen.rglob('*')) if p.is_file()}
    (frozen / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    env['EXPERIMENT_FROZEN_SOURCE'] = str(frozen)
    code = 'import runpy,sys; root=sys.argv.pop(1); module=sys.argv.pop(1); sys.path.insert(0,root); sys.argv[0]=module; runpy.run_module(module,run_name="__main__")'
    print(json.dumps({'frozen_source': str(frozen), 'module': sys.argv[1]}), flush=True)
    return subprocess.call([sys.executable, '-u', '-c', code, str(frozen), *sys.argv[1:]], cwd=root, env=env)


if __name__ == '__main__':
    raise SystemExit(main())
