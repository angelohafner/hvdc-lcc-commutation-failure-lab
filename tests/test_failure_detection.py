"""Hand-defined detector fixtures are test signals, never simulation results."""
import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
try:
    from detect_failures import classify_transfer
    from detect_failures import characterize_sequence
except ImportError:
    classify_transfer=None
    characterize_sequence=None

class FailureDetection(unittest.TestCase):
    def fixture(self,kind='normal'):
        t=np.arange(0.,.00601,.00001)
        out=np.where(t<.001,1000.,0.)
        incoming=1000.-out
        voltage=np.where((t>=.001)&(t<.003),-50000.,20000.)
        voltage=np.where(out>50.,10.,voltage)
        if kind=='low_margin':voltage=np.where((t>=.001)&(t<.0012),-50000.,20000.);voltage[t<.001]=10.
        if kind=='failed':
            out=np.full_like(t,800.);incoming=np.where(t<.0005,0.,200.);voltage=np.full_like(t,8.)
        if kind=='reignition':
            out[t>=.00115]=1000.;incoming[t>=.00115]=0.;voltage[t>=.00115]=10.
        comm=np.where(t<.003,40000.,-40000.)
        return t,out,incoming,voltage,comm,np.full_like(t,1000.)

    def test_success_and_low_margin_are_not_failures(self):
        self.assertIsNotNone(classify_transfer,'Transfer classification is missing')
        for kind,want in [('normal','normal'),('low_margin','reduced_margin')]:
            e=classify_transfer(*self.fixture(kind),frequency=50.,recovery_s=.0002)
            self.assertEqual(e['classification'],want)
            self.assertFalse(e['verified_failure'])

    def test_retained_outgoing_current_after_voltage_reversal_is_failure(self):
        self.assertIsNotNone(classify_transfer)
        e=classify_transfer(*self.fixture('failed'),frequency=50.,recovery_s=.0002)
        self.assertEqual(e['classification'],'unsuccessful_transfer');self.assertTrue(e['verified_failure'])

    def test_resumed_current_without_new_gate_is_one_failure(self):
        self.assertIsNotNone(classify_transfer)
        e=classify_transfer(*self.fixture('reignition'),frequency=50.,recovery_s=.0002)
        self.assertEqual(e['classification'],'resumed_conduction');self.assertTrue(e['verified_failure'])

    def test_missing_voltage_evidence_is_inconclusive(self):
        self.assertIsNotNone(classify_transfer)
        values=list(self.fixture('failed'));values[3]=np.full_like(values[3],np.nan)
        e=classify_transfer(*values,frequency=50.,recovery_s=.0002)
        self.assertEqual(e['classification'],'inconclusive');self.assertFalse(e['verified_failure'])

    def test_returning_current_with_contradictory_voltage_cannot_be_success(self):
        values=list(self.fixture('reignition'))
        values[3][values[0]>=.00115]=20000.
        e=classify_transfer(*values)
        self.assertEqual(e['classification'],'inconclusive')
        self.assertFalse(e['verified_failure'])
        self.assertIsNone(e['gamma_deg'])
        self.assertIsNone(e['current_completion_s'])

    def test_near_zero_current_without_blocking_is_not_resumed_conduction(self):
        values=list(self.fixture('reignition'))
        values[1]=np.maximum(values[1],8.)
        values[3]=values[1]*.01
        e=classify_transfer(*values)
        self.assertEqual(e['classification'],'inconclusive')
        self.assertFalse(e['verified_failure'])
        self.assertIsNone(e['current_completion_s'])
        self.assertIsNone(e['overlap_deg'])

    def test_existing_incoming_current_that_only_decays_is_not_a_new_transfer(self):
        values=list(self.fixture('failed'));values[2]=np.linspace(200.,0.,len(values[0]))
        e=classify_transfer(*values)
        self.assertEqual(e['classification'],'inconclusive');self.assertFalse(e['verified_failure'])

    def test_extinction_at_window_end_remains_inconclusive_without_crashing(self):
        t=np.arange(10)*1e-5;out=np.array([1000.]*7+[0.]*3);incoming=1000.-out
        e=classify_transfer(t,out,incoming,np.where(out>0,10.,-5000.),np.full(10,10000.),np.full(10,1000.))
        self.assertEqual(e['classification'],'inconclusive')

    def test_new_outgoing_gate_prevents_resumed_conduction_claim(self):
        values=self.fixture('reignition');g=np.where(values[0]>=.0011,1.,0.)
        e=classify_transfer(*values,outgoing_gate=g)
        self.assertEqual(e['classification'],'inconclusive')

    def test_post_clearing_failure_is_not_automatically_subsequent(self):
        self.assertIsNotNone(characterize_sequence)
        failed=lambda t:dict(time_s=t,verified_failure=True,classification='unsuccessful_transfer')
        e=[failed(.31),failed(.39),failed(.42)]
        r=characterize_sequence(e,.38)
        self.assertEqual(r['post_clearing_failure_events'],2)
        self.assertEqual(r['subsequent_failure_events'],0)
        e=[failed(.31)]+[dict(time_s=.381+i*.0034,verified_failure=False,classification='normal') for i in range(6)]+[failed(.41)]
        r=characterize_sequence(e,.38)
        self.assertEqual(r['subsequent_failure_events'],1)

    def test_inconclusive_attempt_does_not_erase_established_recovery(self):
        events=[dict(time_s=.40+i*.0034,verified_failure=False,classification='normal') for i in range(6)]
        events += [dict(time_s=.421,verified_failure=False,classification='inconclusive'),
                   dict(time_s=.425,verified_failure=True,classification='unsuccessful_transfer')]
        result=characterize_sequence(events,.38)
        self.assertEqual(result['subsequent_failure_events'],1)
        self.assertIsNone(result['stable_recovery_start_s'])

if __name__=='__main__':unittest.main()
