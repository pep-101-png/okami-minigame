"""Subscription feedback retrieval: no model API or live GitHub required."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec=importlib.util.spec_from_file_location('fetch',Path(__file__).resolve().parents[1]/'fetch_feedback.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
COMMIT='a'*40
RUN='20261021T082129301Z-f00f54'
URL=f'https://github.com/{f.REPO}/releases/download/{f.TAG}/{COMMIT}-{RUN}.zip'


def bundle():
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as z:
        z.writestr('report.json',json.dumps(dict(commit=COMMIT,runId=RUN,validation='passed')))
        z.writestr('video-capture.json',json.dumps(dict(status='failed',error='Gameplay scene/player disappeared.',clips=[
            dict(name='walk-side',status='failed',frames=0,expectedFrames=120,error='Gameplay scene/player disappeared.') ])))
        z.writestr('screenshots\\gameplay-live-camera.png',b'synthetic image fixture')
        z.writestr('videos\\',b'')  # .NET Framework's actual Windows separator shape.
    return data.getvalue()


class FetchTests(unittest.TestCase):
    def test_windows_zip_and_all_fourteen_accounting(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);archive=root/'test.zip';archive.write_bytes(bundle())
            out=root/'out';out.mkdir();f.safe_extract(archive,out)
            self.assertTrue((out/'screenshots/gameplay-live-camera.png').exists())
            index=f.review_index(out)
            self.assertEqual(len(index['clips']),14)
            self.assertEqual(index['clips'][0]['frames'],0)
            self.assertIn('disappeared',index['clips'][0]['error'])
            self.assertEqual(sum(c['captureStatus']=='not_captured' for c in index['clips']),13)
            self.assertTrue(all(not c['videos'] for c in index['clips']))
            self.assertIn('NOT_PERFORMED',index['visualReview'])

    def test_traversal_and_duplicates_after_normalization(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ('..\\outside.log','C:\\outside.log','/outside.log'):
                archive=root/'bad.zip'
                with zipfile.ZipFile(archive,'w') as z:z.writestr(name,'bad')
                with self.assertRaises(ValueError):f.safe_extract(archive,root/'out')
            with zipfile.ZipFile(root/'collision.zip','w') as z:
                z.writestr('screenshots\\x.png','a');z.writestr('screenshots/x.png','b')
            with self.assertRaises(ValueError):f.safe_extract(root/'collision.zip',root/'out')

    def test_verified_download_and_cache_without_api_service(self):
        body=bundle();digest=hashlib.sha256(body).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch.object(f,'urlopen',return_value=io.BytesIO(body)):
                with self.assertRaises(ValueError):f.retrieve(URL,'0'*64,root)
            self.assertFalse((root/RUN).exists())
            with patch.object(f,'urlopen',return_value=io.BytesIO(body)) as download:
                directory=f.retrieve(URL,digest,root)
                self.assertEqual(f.retrieve(URL,digest,root),directory)
                self.assertEqual(download.call_count,1)
            self.assertEqual(f.load_json(directory/'review-index.json')['commit'],COMMIT)
            with self.assertRaises(ValueError):f.retrieve('https://example.com/not-feedback.zip',digest,root)


if __name__=='__main__':unittest.main()
