"""Validate native PSCAD channels and export SI data with valve-level evidence."""
from pathlib import Path
import argparse, hashlib, json, re
import numpy as np
from detect_failures import detect_events,characterize_sequence

ROOT=Path(__file__).resolve().parents[1]

def validate_samples(t,signals,step):
    if len(t)<3 or not np.all(np.isfinite(t)) or not np.allclose(np.diff(t),step,rtol=1e-7,atol=1e-10):
        raise ValueError('Nonuniform, duplicate, or invalid sample times')
    for name,value in signals.items():
        if len(value)!=len(t) or not np.all(np.isfinite(value)):
            raise ValueError(f'Invalid channel {name}')

def read_case(folder):
    folder=Path(folder);r=json.loads((folder/'receipt.json').read_text())
    if r['execution_status']!='success' or r.get('validation_status','').startswith('rejected'):
        raise ValueError('Run is not eligible for validation')
    source_project=folder/Path(r['project']).name
    if not source_project.exists() or hashlib.sha256(source_project.read_bytes()).hexdigest()!=r['project_sha256']:
        raise ValueError('Project hash mismatch')
    for name,want in r['output_sha256'].items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=want:raise ValueError(f'Source hash mismatch: {name}')
    inf=next(folder.glob('*.inf')).read_text()
    metadata=re.findall(r'PGB\((\d+)\).*?Desc="([^"]+)".*?Units="([^"]*)"',inf)
    metadata.sort(key=lambda p:int(p[0]))
    if [int(x[0]) for x in metadata]!=list(range(1,len(metadata)+1)):raise ValueError('Non-contiguous metadata')
    arrays=[np.loadtxt(f,skiprows=1,ndmin=2) for f in sorted(folder.glob('*.out'))]
    t=arrays[0][:,0]
    if any(a.shape[0]!=len(t) or not np.allclose(a[:,0],t,rtol=0,atol=1e-12) for a in arrays):
        raise ValueError('Time columns disagree between native files')
    all_signals=np.concatenate([a[:,1:] for a in arrays],axis=1)
    if all_signals.shape[1]!=len(metadata):raise ValueError('Channel count does not match metadata')
    signals={};units={}
    for column,(_,name,unit) in zip(all_signals.T,metadata):
        if name in signals:raise ValueError('Duplicate channel name')
        factor,new_unit={'kA':(1000.,'A'),'kV':(1000.,'V')}.get(unit,(1.,unit or '1'))
        signals[name]=column*factor;units[name]=new_unit
    step=r['parameters']['time_step_us']*1e-6
    validate_samples(t,signals,step)
    if abs(t[0])>1e-12 or abs(t[-1]-r['parameters']['duration_s'])>step*.1:raise ValueError('Truncated simulation')
    required=['Idc_meas','Vdc_meas']+[f'{s}{k}' for s in ['IT','VT','G'] for k in range(1,7)]
    if any(x not in signals for x in required):raise ValueError('Required valve/DC channel is missing')
    r.update(units=units,source_hashes_verified=True,samples=len(t))
    return t,signals,r

def process_case(folder):
    t,d,r=read_case(folder);p=r['parameters'];events=detect_events(t,d,p)
    before=(t>.22)&(t<min(.28,p['fault_start_s']-.01));late=t>t[-1]-.06
    kcl={name:float(np.max(abs((d['Idc_meas']-sum(d[f'IT{k}'] for k in group))[t>.2])))
         for name,group in [('upper',[1,3,5]),('lower',[2,4,6])]}
    power=-d['Vdc_meas']*d['Idc_meas']
    d['Pdc_to_bridge']=power;r['units']['Pdc_to_bridge']='W'
    # Grid-source current is positive out of the Thevenin source toward the bridge.
    d['Pac_to_grid']=-sum(d['VPCC'+x]*d['IG'+x] for x in 'ABC');r['units']['Pac_to_grid']='W'
    failures=[e for e in events if e['verified_failure']]
    valid_gamma=[e['gamma_deg'] for e in events if e['gamma_deg'] is not None]
    end=p['fault_start_s']+p['fault_duration_s']
    summary=dict(case_id=r['case_id'],title=p['title'],samples=len(t),time_step_us=p['time_step_us'],
                 mean_dc_current_before_A=float(np.mean(d['Idc_meas'][before])),
                 mean_dc_voltage_before_V=float(np.mean(d['Vdc_meas'][before])),
                 mean_power_before_W=float(np.mean(power[before])),
                 mean_grid_power_before_W=float(np.mean(d['Pac_to_grid'][before])),
                 mean_dc_current_final_A=float(np.mean(d['Idc_meas'][late])),
                 dc_ripple_final_fraction=float(np.ptp(d['Idc_meas'][late])/max(1,np.mean(d['Idc_meas'][late]))),
                 peak_dc_current_A=float(np.max(d['Idc_meas'][t>.2])),
                 verified_failure_events=len(failures),
                 **characterize_sequence(events,end),
                 inconclusive_events=sum(e['classification']=='inconclusive' for e in events),
                 min_valid_gamma_deg=min(valid_gamma) if valid_gamma else None,
                 kcl_max_error_A=kcl,execution_status='success',
                 physical_consistency='pass' if max(kcl.values())<max(20.,.01*np.max(d['Idc_meas'])) else 'fail')
    dest=ROOT/'results/processed'/r['case_id'];dest.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(dest/'signals.npz',time=t,**d)
    for name,value in [('metadata',r),('events',events),('summary',summary)]:
        (dest/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False))
    print(json.dumps(summary),flush=True);return t,d,r,events,summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('cases',nargs='*',default=['CF-00','CF-02']);a=ap.parse_args()
    for case in a.cases:process_case(ROOT/'results/raw'/case)
