"""Bounded real-PSCAD studies; no browser or Python transient substitutions."""
import argparse
import mhi.pscad
from run_simulations import run,CASES,ROOT
from process_results import process_case

STUDIES={
 'CF-13-R2':dict(title='Recovery and DC restoration transient',sag_pu=.5,recovery_dc_pu=-.2,recovery_hold_s=.12,restore_overshoot_pu=1.,restore_decay_s=.15,restore_rise_s=.1,duration_s=.9),
 'REC-NOMINAL':dict(title='Recovery with DC suppression and nominal restoration',sag_pu=.5,recovery_dc_pu=-.2,recovery_hold_s=.12,duration_s=.9),
 'SW-SAG-085':dict(title='Refined sag sweep: 0.85 pu',sag_pu=.85),
 'SW-SAG-0875':dict(title='Refined sag sweep: 0.875 pu',sag_pu=.875),
 'CF-13-R1':dict(title='Recovery with prescribed DC restoration overshoot',sag_pu=.5,recovery_dc_pu=.05,recovery_hold_s=.12,restore_overshoot_pu=.5,restore_decay_s=.05,duration_s=.8),
 'REC-SMOOTH':dict(title='Recovery with nominal DC voltage restoration',sag_pu=.5,recovery_dc_pu=.05,recovery_hold_s=.12,restore_overshoot_pu=0.,duration_s=.8),
 'SW-SAG-065':dict(title='Sag sweep: 0.65 pu',sag_pu=.65),
 'SW-SAG-080':dict(title='Sag sweep: 0.80 pu',sag_pu=.8),
 'SW-SAG-090':dict(title='Sag sweep: 0.90 pu',sag_pu=.9),
 'REC-010':dict(title='Recovery study: 10 ms sag',sag_pu=.5,fault_duration_s=.01),
 'MIT-ANGLE':dict(title='Mitigation: temporary firing advance',sag_pu=.5,alpha_event_deg=120.),
 'MIT-DC':dict(title='Mitigation: reduced DC source voltage',sag_pu=.5,dc_reduce_pu=.35),
 'MIT-COMBINED':dict(title='Mitigation: firing advance and DC voltage reduction',sag_pu=.5,alpha_event_deg=125.,dc_reduce_pu=.65),
 'NUM-BASE-5US':dict(**CASES['CF-00'],time_step_us=5.),
 'NUM-SAG-5US':dict(**CASES['CF-02'],time_step_us=5.),
 'INCEPTION-90':dict(title='Sag inception shifted by 90 electrical degrees',sag_pu=.5,fault_start_s=.305),
}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=0);ap.add_argument('--cases',nargs='+',default=list(STUDIES));args=ap.parse_args()
    a=mhi.pscad.connect(port=args.port)
    for name in args.cases:
        folder=ROOT/'results/raw'/name
        if not folder.exists():run(a,name,STUDIES[name])
        process_case(folder)
