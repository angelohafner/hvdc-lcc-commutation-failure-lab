"""Reject wrong short source disturbances even when the record median looks good."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'python'))
import validate_study


@unittest.skipUnless((ROOT/'results/processed/CF-02/signals.npz').exists(), 'Native-derived local arrays required')
class SourceProfiles(unittest.TestCase):
    def reject_modified_profile(self, case, parameter, value):
        original = json.loads
        target = (ROOT/f'results/processed/{case}/metadata.json').read_text()

        def modified(text, *args, **kwargs):
            data = original(text, *args, **kwargs)
            if text == target:
                data['parameters'][parameter] = value
            return data

        # Parse real native-derived arrays; suppress only report output during this negative test.
        with patch.object(validate_study.json, 'loads', side_effect=modified), patch.object(Path, 'write_text'), contextlib.redirect_stdout(io.StringIO()):
            result = validate_study.audit()
        row = next(r for r in result['cases'] if r['case_id'] == case)
        self.assertFalse(row['pass'], 'A wrong short source disturbance must fail the engineering audit')
        self.assertFalse(result['pass_all'])

    def test_omitted_ac_sag_is_rejected(self):
        self.reject_modified_profile('CF-02', 'sag_pu', 1.)

    def test_omitted_dc_step_is_rejected(self):
        self.reject_modified_profile('CF-08', 'dc_step_pu', 1.)
