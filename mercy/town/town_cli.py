#!/usr/local/bin/python
"""Public CLI for the isolated workspace; it has no orchestration credential."""
import json
import os
import sys
import urllib.request


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('help', '--help'):
        print('Usage: town TOOL [JSON_ARGUMENTS]\nExamples: town look\n  town go \'{"destination":"hall"}\'\n  town people_here\nOnly public investigation actions are available. Use the tool schemas supplied to the detective. Local files do not establish evidence.')
        return
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    body = {'action': sys.argv[1], 'args': args}
    req = urllib.request.Request(os.getenv('TOWN_GATEWAY_URL', 'http://harness:8002').rstrip('/') + '/tool',
                                 data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=55) as response:
        print(response.read(20000).decode('utf-8'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print(json.dumps({'error': 'Public town action unavailable; use valid arguments or another tool'}))
        raise SystemExit(1)
