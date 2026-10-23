"""Package the two files required to repair the reported Unity CS0619 error."""
from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'download-output/Sunward-Safe-Mode-Fix.zip'
SCRIPT = 'Assets/Sunward/Scripts/ResidentLocomotion.cs'


def main():
    source = ROOT / 'Sunward-Unity' / SCRIPT
    assert 'GetInstanceID(' not in source.read_text()
    assert 'stepSource.pitch = 1f;' in source.read_text()
    OUTPUT.parent.mkdir(exist_ok=True)
    files = {name: (ROOT / 'Sunward-Unity' / name).read_bytes()
             for name in (SCRIPT, SCRIPT + '.meta')}
    with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(files)
        for name, data in files.items():
            assert archive.read(name) == data
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    OUTPUT.with_suffix('.zip.sha256').write_text(digest + '  ' + OUTPUT.name + '\n')
    print('PASS: two-file Unity fix ZIP;', OUTPUT.stat().st_size, 'bytes; SHA256', digest)


if __name__ == '__main__':
    main()
