"""Check browser bytes against independent full-precision event CSV exports."""
import base64,hashlib,json,unittest,zlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

class ExportedData(unittest.TestCase):
    def test_all_manifest_files_have_the_declared_hash_and_event_totals(self):
        manifest=json.loads((ROOT/'docs/data/manifest.json').read_text())
        for entry in manifest['cases']:
            data=(ROOT/'docs'/entry['file']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),entry['sha256'],entry['id'])
            payload=json.loads(data.decode()[len('window.registerCase('):-2])
            self.assertEqual(sum(e['verified_failure'] for e in payload['events']),entry['summary']['verified_failure_events'])

    def test_browser_encoding_preserves_selected_native_samples(self):
        for case in ['CF-00','CF-02','CF-13-R2','MIT-DC']:
            text=(ROOT/f'docs/data/cases/{case}.js').read_text();p=json.loads(text[len('window.registerCase('):-2])
            raw=zlib.decompress(base64.b64decode(p['data']));n=p['samples'];f=len(p['fields'])
            if p.get('data_layout')=='xor-byteplanes-v1':
                words=np.frombuffer(raw,dtype='u1').reshape(f,4,n).transpose(0,2,1).copy().view('<u4').reshape(f,n)
                a=np.bitwise_xor.accumulate(words,axis=1).view('<f4').T
            else:a=np.frombuffer(raw,dtype='<f4').reshape(n,f)
            csv=np.genfromtxt(ROOT/f'results/validated_samples/{case}_event.csv',delimiter=',',names=True)
            indices=np.rint((csv['time']-p['t0'])/p['dt']).astype(int)
            for key in csv.dtype.names:
                if key=='time':continue
                np.testing.assert_array_equal(a[indices,p['fields'].index(key)],csv[key].astype('float32'),err_msg=case+' '+key)

if __name__=='__main__':unittest.main()
