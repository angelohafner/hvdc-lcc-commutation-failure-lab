"""Timing, integrity, and provenance failure tests."""
import sys, unittest, tempfile, json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
try:
    from process_results import validate_samples, read_case
except ImportError:
    validate_samples=read_case=None

class DataPipeline(unittest.TestCase):
    def test_timing_contract_rejects_duplicates_gaps_and_nan(self):
        self.assertIsNotNone(validate_samples,'Sample validation is not implemented')
        for t in [[0.,.001,.001],[0.,.001,.003],[0.,.001,float('nan')]]:
            with self.assertRaises(ValueError):validate_samples(np.array(t),{'I':np.ones(3)},.001)
        with self.assertRaises(ValueError):validate_samples(np.array([0.,.001,.002]),{'I':np.array([1.,np.nan,2.])},.001)

    def test_native_data_has_si_units_and_source_provenance(self):
        if not (Path(__file__).resolve().parents[1]/'results/raw/CF-00/receipt.json').exists():self.skipTest('Native evidence is local; reproduce PSCAD runs first')
        self.assertIsNotNone(read_case,'PSCAD ingestion is not implemented')
        t,d,meta=read_case(Path(__file__).resolve().parents[1]/'results/raw/CF-00')
        self.assertEqual(len(t),60001)
        self.assertEqual(meta['units']['Idc_meas'],'A')
        self.assertGreater(np.mean(d['Idc_meas'][t>.5]),1000.)
        self.assertLess(np.mean(d['Idc_meas'][t>.5]),2000.)
        self.assertTrue(meta['source_hashes_verified'])

    def test_mismatched_project_is_rejected_before_reading_channels(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'case.pscx').write_text('changed project')
            (root/'receipt.json').write_text(json.dumps(dict(execution_status='success',project='pscad/case.pscx',project_sha256='0'*64,output_sha256={'missing.out':'0'*64})))
            with self.assertRaisesRegex(ValueError,'Project hash mismatch'):read_case(root)

if __name__=='__main__':unittest.main()
