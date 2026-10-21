"""Synthetic integration tests; never call GitHub, OpenAI or Unity."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

MODULE = Path(__file__).resolve().parents[1] / 'feedback_receiver.py'
spec = importlib.util.spec_from_file_location('receiver', MODULE)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ReceiverTests(unittest.TestCase):
    def test_validation_and_scope(self):
        p = dict(commit='a'*40, run_id='20261021T120000000Z-abcdef', sha256='b'*64)
        p['asset'] = p['commit']+'-'+p['run_id']+'.zip'
        self.assertEqual(r.payload(dict(action='sunward_unity_feedback', client_payload=p)), p)
        for key, value in [('commit', '$(touch BAD)'), ('asset', '../../bad.zip'), ('sha256', 'x')]:
            with self.assertRaises(ValueError):
                r.payload(dict(action='sunward_unity_feedback', client_payload={**p, key: value}))
        for bad in ['Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity', '.github/workflows/x.yml',
                    'tools/windows-sync/Sync.ps1', 'tools/unity-automation/../windows-sync/a.ps1']:
            with self.assertRaises(ValueError):
                r.check_paths([bad])
        r.check_paths(['tools/unity-automation/Common.ps1'])

    def test_zip_safety(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('../escape.log', '/absolute.log', 'C:/bad.log', 'x\\bad.log', 'bad.exe'):
                archive = root/'bad.zip'
                with zipfile.ZipFile(archive, 'w') as z:
                    z.writestr(name, 'bad')
                with self.assertRaises(ValueError):
                    r.extract(archive, root/'out')
            with zipfile.ZipFile(root/'good.zip', 'w') as z:
                z.writestr('report.json', '{}')
                z.writestr('videos/fallback-frames.zip', 'not recursively extracted')
            r.extract(root/'good.zip', root/'safe')
            self.assertTrue((root/'safe/report.json').exists())
            self.assertFalse((root/'safe/videos/fallback-frames.zip').exists())

    def test_local_delivery_to_review_branch(self):
        """Real Git/ZIP prepare and finish, fake gh and fake agent patch."""
        with tempfile.TemporaryDirectory() as temp:
            old = Path.cwd()
            root = Path(temp)
            repo = root/'repo';repo.mkdir()
            real_run = r.run
            calls = []
            try:
                os.chdir(repo)
                real_run('git', 'init', '-b', r.TARGET)
                real_run('git', 'config', 'user.name', 'Fixture')
                real_run('git', 'config', 'user.email', 'fixture@example.invalid')
                source = Path('tools/unity-automation')
                source.mkdir(parents=True)
                (source/'Common.ps1').write_text('# before\n')
                real_run('git', 'add', '.')
                real_run('git', 'commit', '-m', 'fixture')
                base = real_run('git', 'rev-parse', 'HEAD').stdout.strip()
                remote = root/'remote.git'
                real_run('git', 'init', '--bare', str(remote))
                real_run('git', 'remote', 'add', 'origin', str(remote))
                real_run('git', 'push', 'origin', r.TARGET)
                run_id = '20261021T120000000Z-abcdef'
                name = base+'-'+run_id+'.zip'
                archive = root/name
                with zipfile.ZipFile(archive, 'w') as z:
                    z.writestr('report.json', json.dumps(dict(commit=base, runId=run_id, status='failed')))
                    z.writestr('validation-editor.log', 'synthetic compilation failure')
                event = dict(action='sunward_unity_feedback', client_payload=dict(commit=base, run_id=run_id,
                            asset=name, sha256=hashlib.sha256(archive.read_bytes()).hexdigest()))
                event_file=root/'event.json';event_file.write_text(json.dumps(event))
                output=root/'output';output.write_text('')
                def fake(*args, **kwargs):
                    if args[0] != 'gh':
                        return real_run(*args, **kwargs)
                    calls.append(args)
                    if args[1:3] == ('pr', 'list'):
                        return subprocess.CompletedProcess(args, 0, '[]', '')
                    if args[1] == 'api':
                        ref = args[2].split('/git/ref/heads/')[1]
                        found = real_run('git', 'ls-remote', 'origin', 'refs/heads/'+ref).stdout.split()
                        return subprocess.CompletedProcess(args, 0 if found else 1, found[0] if found else '', '')
                    if args[1:3] == ('release', 'download'):
                        shutil.copyfile(archive, Path('feedback')/name)
                    return subprocess.CompletedProcess(args, 0, '', '')
                with patch.dict(os.environ, GITHUB_EVENT_PATH=str(event_file), GITHUB_OUTPUT=str(output), REPAIR_BASE=base), patch.object(r, 'run', side_effect=fake):
                    # A dispatch hash is binding, not advisory.
                    correct_hash=event['client_payload']['sha256']
                    event['client_payload']['sha256']='0'*64
                    event_file.write_text(json.dumps(event))
                    with self.assertRaises(ValueError):
                        r.prepare()
                    shutil.rmtree('feedback')
                    event['client_payload']['sha256']=correct_hash
                    event_file.write_text(json.dumps(event))
                    r.prepare()
                    self.assertIn('run=true', output.read_text())
                    self.assertTrue(Path('feedback/artifacts/validation-editor.log').exists())
                    (source/'Common.ps1').write_text('# synthetic agent repair\n')
                    r.finish()
                    self.assertTrue(any(c[1:3] == ('pr', 'create') and '--draft' in c for c in calls))
                    self.assertEqual(real_run('git', 'ls-remote', 'origin', f'refs/heads/{r.TARGET}').stdout.split()[0], base)
                    self.assertIn(r.branch_for(base), real_run('git', 'ls-remote', 'origin').stdout)
                    # Duplicate event should skip agent invocation, not create another repair.
                    real_run('git', 'checkout', '--detach', base)
                    output.write_text('')
                    r.prepare()
                    self.assertIn('run=false', output.read_text())
            finally:
                os.chdir(old)


if __name__ == '__main__':
    unittest.main()
