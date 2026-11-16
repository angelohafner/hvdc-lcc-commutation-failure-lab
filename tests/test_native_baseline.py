"""Integration checks against actual native PSCAD output; no synthetic replacement."""
import json
from pathlib import Path
import unittest
import re
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless((ROOT/'results/raw/CF-00/receipt.json').exists(),'Native evidence is local; reproduce PSCAD runs first')
class NativeBaseline(unittest.TestCase):
    def test_completed_native_run_has_fresh_channel_evidence(self):
        path=ROOT/'results/raw/CF-00/receipt.json'
        self.assertTrue(path.exists(), 'The baseline has not been executed')
        r=json.loads(path.read_text())
        self.assertEqual(r['execution_status'],'success')
        self.assertTrue(r['licensed'])
        self.assertGreaterEqual(len(r['output_sha256']),5)
        self.assertFalse(r['errors'])

    def test_dc_current_returns_through_both_valve_groups(self):
        folder=ROOT/'results/raw/CF-00'
        names=re.findall('Desc="([^"]+)"',next(folder.glob('*.inf')).read_text())
        arrays=[np.loadtxt(f,skiprows=1) for f in sorted(folder.glob('*.out'))]
        data=dict(zip(names,np.concatenate([a[:,1:] for a in arrays],axis=1).T))
        window=arrays[0][:,0]>0.5
        for group in [[1,3,5],[2,4,6]]:
            error=data['Idc_meas']-sum(data[f'IT{k}'] for k in group)
            self.assertLess(np.max(np.abs(error[window])),0.02,'Unintended DC return path')

if __name__=='__main__':unittest.main()
