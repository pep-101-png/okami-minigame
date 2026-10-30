"""Retrieve explicitly named original LFS inputs, preserving manifest hashes.

Outputs belong in a separate working directory, never over source resources.
Uses the existing authenticated Git remote and preserves normal proxy settings.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess

def fetch(repo, manifest, output, paths):
    manifest = json.loads(manifest.read_text(encoding='utf-8-sig'))
    files = {r['path']: r for r in manifest['files']}
    output.mkdir(parents=True, exist_ok=True)
    for name in paths:
        record = files[name]
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.stat().st_size == record['bytes']
            assert hashlib.file_digest(target.open('rb'), 'sha256').hexdigest() == record['sha256']
            print('CACHED', name, flush=True)
            continue
        pointer = subprocess.check_output(['git', 'show', 'a82c3b64d451cdd7058f3eb8d0f9dc73723ad53d:' + name], cwd=repo)
        assert pointer.startswith(b'version https://git-lfs.github.com/spec/v1')
        temporary = target.with_name(target.name + '.partial')
        try:
            with temporary.open('wb') as stream:
                subprocess.run(['git', 'lfs', 'smudge', name], input=pointer, stdout=stream, cwd=repo, check=True)
            assert temporary.stat().st_size == record['bytes']
            assert hashlib.file_digest(temporary.open('rb'), 'sha256').hexdigest() == record['sha256']
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        print('VERIFIED', name, record['bytes'], flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('paths', nargs='+')
    a = p.parse_args()
    fetch(a.repo, a.manifest, a.output, a.paths)
