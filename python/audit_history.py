"""Scan only the Git history selected for publication; never print matched secrets."""
import argparse
import getpass
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SECRET = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{35,}|sk-[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')


def audit(ref='HEAD'):
    revision = subprocess.check_output(['git', 'rev-parse', '--verify', ref+'^{commit}'], cwd=ROOT, text=True).strip()
    objects = subprocess.check_output(['git', 'rev-list', '--objects', revision], cwd=ROOT, text=True).splitlines()
    issues = []
    scanned = 0
    with subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as process:
        for item in objects:
            oid, _, name = item.partition(' ')
            process.stdin.write((oid+'\n').encode())
            process.stdin.flush()
            header = process.stdout.readline().decode().split()
            size = int(header[2])
            data = process.stdout.read(size)
            process.stdout.read(1)
            if header[1] != 'blob':
                continue
            scanned += 1
            kinds = []
            if SECRET.search(data):
                kinds.append('Credential-like pattern')
            if getpass.getuser().encode() in data:
                kinds.append('Local OS-account stamp')
            if size > 50*1024*1024:
                kinds.append('Blob exceeds 50 MiB release policy')
            if kinds:
                issues.append(dict(object=oid, path=name, kinds=kinds))
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError('Git history scan did not complete')
    return dict(scope='All blobs reachable from the selected publication commit', commit=revision,
                blobs_scanned=scanned, issues=issues, passed=not issues)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--output', default='reports/history_audit.json')
    args = parser.parse_args()
    result = audit(args.ref)
    (ROOT/args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
