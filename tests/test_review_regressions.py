"""Regression contracts for the independent final review findings."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
from detect_failures import detect_events
import run_simulations

class ReviewRegressions(unittest.TestCase):
    @unittest.skipUnless((ROOT/'results/processed/CF-09/signals.npz').exists(),'Native-derived local array required')
    def test_actual_gate_bounds_angle_change_attempt(self):
        folder=ROOT/'results/processed/CF-09';z=dict(np.load(folder/'signals.npz'));p=json.loads((folder/'metadata.json').read_text())['parameters']
        events=detect_events(z['time'],z,p)
        e=next(e for e in events if abs(e['time_s']-.3)<1e-8 and e['incoming']=='T2')
        self.assertLess(e['window_end_s'],.301)
        self.assertEqual(e['classification'],'inconclusive')
        for e in events:
            group=[1,3,5] if int(e['incoming'][1:])%2 else [2,4,6]
            for k in group:
                rises=np.flatnonzero(np.diff(z[f'G{k}'])>.5)+1
                self.assertFalse(any(e['time_s']<z['time'][i]<=e['window_end_s'] for i in rises))

    def test_existing_evidence_refuses_run_before_any_pscad_or_file_mutation(self):
        class NoAccess:
            def project_names(self):raise AssertionError('PSCAD accessed before refusing existing evidence')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'results/raw/EXISTS').mkdir(parents=True)
            with patch.object(run_simulations,'ROOT',root):
                with self.assertRaises(FileExistsError):run_simulations.run(NoAccess(),'EXISTS',{'alpha_deg':170.})

if __name__=='__main__':unittest.main()
