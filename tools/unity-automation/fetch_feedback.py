"""Retrieve existing Unity feedback for an active Codex subscription task.
No model API, paid service, background task, repository write or PC connection.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
import zipfile

REPO = 'pep-101-png/okami-minigame'
TAG = 'sunward-unity-feedback'
MAX_BYTES = 140 * 1024 * 1024
EXPECTED = [f'{gait}-{angle}' for gait in ('walk', 'jog', 'sprint')
            for angle in ('side', 'front', 'rear-quarter')] + [
    'jump-air-land-side', 'gait-stop-turn-side', 'dodge-directions-rear-quarter',
    'combat-light-heavy-charge-side', 'windflower-gameplay-route']


def safe_extract(archive, destination):
    total = 0
    with zipfile.ZipFile(archive) as z:
        if len(z.infolist()) > 2048:
            raise ValueError('Too many ZIP entries')
        for item in z.infolist():
            # .NET Framework ZIPs on Windows can use backslashes. Normalize first,
            # then reject traversal, drive names and duplicate normalized names.
            name = item.filename.replace('\\', '/')
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or ':' in name or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError('Unsafe ZIP entry: '+item.filename)
            total += item.file_size
            if total > MAX_BYTES:
                raise ValueError('ZIP decompression budget exceeded')
            if item.is_dir() or name.endswith('/'):
                continue
            if path.suffix.lower() not in ('.json', '.xml', '.log', '.csv', '.png', '.mp4', '.zip'):
                raise ValueError('Unexpected feedback artifact type')
            target = destination.joinpath(*path.parts)
            if target.exists():
                raise ValueError('Duplicate normalized ZIP entry')
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(item) as source, target.open('xb') as out:
                shutil.copyfileobj(source, out, 1024*1024)


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}


def review_index(directory):
    report = load_json(directory/'report.json')
    capture = load_json(directory/'video-capture.json')
    encoding = load_json(directory/'video-report.json')
    clips = []
    for name in EXPECTED:
        sources = [c for c in capture.get('clips', []) if c.get('name') == name]
        source = sources[0] if len(sources) == 1 else {}
        encoded = next((c for c in encoding.get('clips', []) if c.get('name') == name), {})
        videos = sorted(str(p.relative_to(directory)) for p in (directory/'videos').glob(name+'.mp4'))
        clips.append(dict(name=name, captureStatus=source.get('status', 'not_captured'),
                          frames=source.get('frames', 0), expectedFrames=source.get('expectedFrames'),
                          error=source.get('error') or ('No unique capture entry' if not source else ''),
                          encodingStatus=encoded.get('status', 'not_run'), videos=videos))
    return dict(commit=report.get('commit'), runId=report.get('runId'),
                validation=report.get('validation'), captureError=capture.get('error'),
                screenshots=sorted(str(p.relative_to(directory)) for p in (directory/'screenshots').glob('*.png')),
                clips=clips, visualReview='NOT_PERFORMED: open actual images/video frames in the active Codex task')


def retrieve(url, digest, output):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != 'github.com' or not parsed.path.startswith(f'/{REPO}/releases/download/{TAG}/'):
        raise ValueError('Only the existing repository feedback release is supported')
    match = re.fullmatch(r'([0-9a-f]{40})-(\d{8}T\d{9}Z-[0-9a-f]{6})\.zip', Path(parsed.path).name)
    if not match or not re.fullmatch('[0-9a-f]{64}', digest):
        raise ValueError('Invalid feedback identity/hash')
    output.mkdir(parents=True, exist_ok=True)
    final = output/match.group(2)
    if final.exists():
        receipt = load_json(final/'download-receipt.json')
        if receipt.get('sha256') == digest and receipt.get('url') == url:
            return final  # Immutable download cache, never rerun Unity or re-upload.
        raise ValueError('Existing feedback directory has a different/unverified identity')
    work = Path(tempfile.mkdtemp(prefix='feedback-', dir=output))
    try:
        archive = work/'download.zip'
        sha = hashlib.sha256()
        size = 0
        with urlopen(url, timeout=60) as source, archive.open('xb') as target:
            while chunk := source.read(1024*1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError('Feedback download exceeds budget')
                sha.update(chunk); target.write(chunk)
        if sha.hexdigest() != digest:
            raise ValueError('Release asset SHA-256 mismatch')
        data = work/'artifacts'
        data.mkdir()
        safe_extract(archive, data)
        report = load_json(data/'report.json')
        if report.get('commit') != match.group(1) or report.get('runId') != match.group(2):
            raise ValueError('Release asset/report identity mismatch')
        (data/'download-receipt.json').write_text(json.dumps(dict(url=url, sha256=digest, bytes=size), indent=2))
        (data/'review-index.json').write_text(json.dumps(review_index(data), indent=2))
        data.rename(final)
        return final
    finally:
        shutil.rmtree(work)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-url')
    parser.add_argument('--sha256')
    parser.add_argument('--commit', help='Optional exact source commit to select')
    parser.add_argument('--output', type=Path, default=Path(tempfile.gettempdir())/'SunwardFeedback')
    args = parser.parse_args()
    if not args.asset_url:
        r = subprocess.run(['gh', 'api', f'repos/{REPO}/releases/tags/{TAG}'], capture_output=True, text=True, timeout=60)
        if r.returncode:
            raise SystemExit('CLI release metadata unavailable. In Codex use the connected GitHub fetch tool for this release, '
                             'then pass its browser_download_url and digest with --asset-url / --sha256. No user file transfer is needed.')
        assets = [a for a in json.loads(r.stdout)['assets'] if a['name'].endswith('.zip') and
                  (not args.commit or a['name'].startswith(args.commit+'-'))]
        if not assets:
            raise SystemExit('No uploaded feedback matches this commit')
        asset = max(assets, key=lambda a: a['created_at'])
        args.asset_url = asset['browser_download_url'];args.sha256 = asset['digest'].removeprefix('sha256:')
    if not args.sha256:
        parser.error('--sha256 is required with --asset-url')
    directory = retrieve(args.asset_url, args.sha256, args.output)
    print(json.dumps(dict(directory=str(directory), index=str(directory/'review-index.json'))))


if __name__ == '__main__':
    main()
