"""Package the exact reviewed project snapshot, with fully retrieved LFS assets."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PROJECT = ROOT / 'Sunward-Unity'
OUTPUT = ROOT / 'download-output' / 'Sunward-Player-Fixes-2-2026-10-23.zip'
MANIFEST = json.loads((HERE / 'project-manifest.json').read_text())
IDLE = 'Sunward-Unity/Assets/Sunward/Generated/Animations/Idle_Natural.anim'


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    expected = {item['path']: item for item in MANIFEST['files']}
    files = sorted(p for name in ('Assets', 'Packages', 'ProjectSettings')
                   for p in (PROJECT / name).rglob('*') if p.is_file())
    actual = {p.relative_to(ROOT).as_posix() for p in files}
    if actual != set(expected):
        raise RuntimeError('Project file list differs from the packaged snapshot: '
                           + str(sorted(actual.symmetric_difference(expected))))
    for path in files:
        item = expected[path.relative_to(ROOT).as_posix()]
        if path.stat().st_size < 1024:
            if path.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise RuntimeError('Unretrieved Git LFS pointer: ' + str(path))
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise RuntimeError('Project asset does not match verified snapshot: ' + str(path))
    if (ROOT / IDLE).stat().st_size != 159951318:
        raise RuntimeError('Full Idle_Natural animation is missing')
    if digest(ROOT / IDLE) != 'ec366136a5252c2354ae11403097d4d43fb2e18d6ef0bc477c79e9fc36ca8375':
        raise RuntimeError('Idle_Natural SHA-256 mismatch')
    OUTPUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in ('Assets', 'Packages', 'ProjectSettings'):
            for directory in [PROJECT / name, *sorted(p for p in (PROJECT / name).rglob('*') if p.is_dir())]:
                archive.write(directory, directory.relative_to(ROOT).as_posix() + '/')
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        for name in ('START-HERE.txt', 'CHANGES-AND-CHECKS.md'):
            archive.write(HERE / name, name)
        archive.write(HERE / 'project-manifest.json', 'PACKAGE-CONTENTS.json')
        archive.write(ROOT / 'tools/living-world/verification-report.json', 'CHECK-RESULTS.json')
    with zipfile.ZipFile(OUTPUT) as archive:
        for name, item in expected.items():
            sha = hashlib.sha256()
            size = 0
            with archive.open(name) as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    sha.update(chunk)
                    size += len(chunk)
            if size != item['bytes'] or sha.hexdigest() != item['sha256']:
                raise RuntimeError('ZIP round-trip validation failed: ' + name)
    sha = digest(OUTPUT)
    OUTPUT.with_suffix('.zip.sha256').write_text(sha + '  ' + OUTPUT.name + '\n')
    print(f'Verified {len(files)} complete project files; ZIP {OUTPUT.stat().st_size} bytes; SHA256 {sha}')


if __name__ == '__main__':
    main()
