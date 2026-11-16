"""Validate the standalone artifact against authoritative browser and native data."""
import base64
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
import zlib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))

class SingleFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=ROOT/'dist/HVDC_LCC_Virtual_Laboratory.html'
        if not cls.path.exists():
            from build_single_file import build
            build(cls.path)
        if cls.path.exists():
            text=cls.path.read_text(encoding='utf-8')
            cls.bundle=json.loads(re.search(r'<script id="single-file-bundle" type="application/json">(.*?)</script>',text,re.S).group(1))

    def test_artifact_contains_every_module_report_font_and_license(self):
        self.assertTrue(self.path.exists(),'Build the requested single-file artifact')
        b=self.bundle
        self.assertEqual(set(b['pages']),{str(i) for i in range(8)}|{'report'})
        self.assertEqual(len(b['recordings']),29)
        self.assertIn('Permission is hereby granted',b['notices']['Project license'])
        self.assertIn('KaTeX',b['notices'])
        css=b['resources']['assets/vendor/katex/katex.min.css']
        urls=re.findall(r'url\(([^)]+)\)',css)
        self.assertGreater(len(urls),20)
        self.assertTrue(all(u.startswith('data:font/') for u in urls))
        for page in b['pages'].values():
            self.assertNotRegex(page['html'],r'<script[^>]+src=|<link[^>]+rel="stylesheet"')
            for src in re.findall(r'<img[^>]+src="([^"]+)"',page['html']):
                self.assertTrue(src.startswith('data:'),src)

    def test_every_embedded_payload_equals_the_verified_source(self):
        self.assertTrue(self.path.exists(),'Build the requested single-file artifact')
        for entry in self.bundle['manifest']['cases']:
            raw=(ROOT/'docs'/entry['file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
            source=json.loads(raw.decode()[len('window.registerCase('):-2])
            self.assertEqual(self.bundle['recordings'][entry['id']],source,entry['id'])

    @unittest.skipUnless((ROOT/'results/processed/CF-00/signals.npz').exists(),'Native-derived local arrays required')
    def test_all_embedded_samples_equal_native_derived_float32_values(self):
        self.assertTrue(self.path.exists(),'Build the requested single-file artifact')
        sample_count=value_count=0
        for case,p in self.bundle['recordings'].items():
            raw=zlib.decompress(base64.b64decode(p['data']));n=p['samples'];f=len(p['fields'])
            words=np.frombuffer(raw,dtype='u1').reshape(f,4,n).transpose(0,2,1).copy().view('<u4').reshape(f,n)
            data=np.bitwise_xor.accumulate(words,axis=1).view('<f4')
            with np.load(ROOT/f'results/processed/{case}/signals.npz') as native:
                mask=native['time']>=.2
                np.testing.assert_allclose(p['t0']+np.arange(n)*p['dt'],native['time'][mask],rtol=0,atol=1e-12)
                for j,key in enumerate(p['fields']):
                    np.testing.assert_array_equal(data[j],native[key][mask].astype('<f4'),err_msg=case+' '+key)
            sample_count+=n;value_count+=n*f
        self.assertEqual(sample_count,1270029)
        self.assertEqual(value_count,43180986)

if __name__=='__main__':unittest.main()
