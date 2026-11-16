"""Engineering audit of accepted PSCAD recordings and numerical sensitivity."""
from pathlib import Path
import json, math
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def source_segments(t, parameters):
    """Keep short disturbances visible instead of diluting them in a record median."""
    start=parameters['fault_start_s'];clear=start+parameters['fault_duration_s']
    hold_end=clear+parameters.get('recovery_hold_s',0.)
    bounds=sorted({.2,float(t[-1]),*[x for x in [start,clear,hold_end] if .2<x<t[-1]]})
    segments=[]
    for lo,hi in zip(bounds,bounds[1:]):
        mask=(t>lo+.001)&(t<hi-.001)
        label='pre_event' if hi<=start else 'disturbance' if lo<clear else 'dc_suppression' if lo<hold_end else 'restoration'
        segments.append((dict(phase=label,start_s=lo,end_s=hi,samples=int(mask.sum()),
                              transition_exclusion_s=.001,ac_median_residual_V={}),mask))
    return segments

def audit():
    rows=[]
    for folder in sorted((ROOT/'results/processed').iterdir()):
        if not (folder/'metadata.json').exists():continue
        m=json.loads((folder/'metadata.json').read_text());p=m['parameters'];z=np.load(folder/'signals.npz');t=z['time']
        events=json.loads((folder/'events.json').read_text());s=json.loads((folder/'summary.json').read_text())
        active=(t>=p['fault_start_s'])&(t<p['fault_start_s']+p['fault_duration_s']);steady=t>.5
        # The source current is positive from its source toward the PCC.
        residual=[];segments=source_segments(t,p)
        for phase,offset in [('A',0),('B',-120),('C',120)]:
            th=360*p['frequency_hz']*t+offset
            expected=p['ac_voltage_v']*np.sqrt(2/3)*((1+active*(p['sag_pu']-1))*np.sin(np.deg2rad(th+active*p['phase_jump_deg']))+active*p['harmonic_pu']*np.sin(np.deg2rad(5*th)))
            actual=z['VPCC'+phase]+p['grid_resistance_ohm']*z['IG'+phase]+p['grid_inductance_h']*np.gradient(z['IG'+phase],t)
            mask=(t>.2)&(abs(t-p['fault_start_s'])>.001)&(abs(t-p['fault_start_s']-p['fault_duration_s'])>.001)
            residual.append(float(np.median(abs(actual[mask]-expected[mask]))))
            for segment,segment_mask in segments:
                segment['ac_median_residual_V'][phase]=float(np.median(abs(actual[segment_mask]-expected[segment_mask]))) if segment['samples']>=3 else None
        ids=[e['event_id'] for e in events]
        factor=1+active*(p['dc_step_pu']*p['dc_reduce_pu']-1)
        after=t-p['fault_start_s']-p['fault_duration_s'];hold=p.get('recovery_hold_s',0.)
        if hold>0:
            factor[(after>=0)&(after<hold)]=p['recovery_dc_pu']
            u=np.maximum(0,after-hold);restored=1+p.get('restore_overshoot_pu',0.)*np.exp(-u/p.get('restore_decay_s',.05))
            if p.get('restore_rise_s',0)>0:restored=1+(restored-1)*(1-np.exp(-u/p['restore_rise_s']))
            factor[after>=hold]=restored[after>=hold]
        dc_actual=p['dc_resistance_ohm']*z['Idc_meas']+p['smoothing_h']*np.gradient(z['Idc_meas'],t)-z['Vdc_meas']
        dc_error=float(np.median(abs(dc_actual[t>.2]-p['dc_voltage_v']*factor[t>.2])))
        for segment,segment_mask in segments:
            segment['dc_median_residual_V']=float(np.median(abs(dc_actual[segment_mask]-p['dc_voltage_v']*factor[segment_mask]))) if segment['samples']>=3 else None
            segment['pass']=segment['samples']>=3 and all(v<1000. for v in segment['ac_median_residual_V'].values()) and segment['dc_median_residual_V']<1000.
        row=dict(case_id=folder.name,execution=m['execution_status'],channels=len(m['units']),source_hashes_verified=m['source_hashes_verified'],
                 native_samples=m['samples'],ac_source_median_residual_V=max(residual),
                 dc_source_median_residual_V=dc_error,
                 source_profile_segments=[s for s,_ in segments],
                 gate_event_window_max_error=float(np.max(abs(z['FaultActive'][(t>.21)&(abs(t-p['fault_start_s'])>.00002)&(abs(t-p['fault_start_s']-p['fault_duration_s'])>.00002)]-active[(t>.21)&(abs(t-p['fault_start_s'])>.00002)&(abs(t-p['fault_start_s']-p['fault_duration_s'])>.00002)]))),
                 max_kcl_residual_A=max(s['kcl_max_error_A'].values()),unique_firing_event_ids=len(ids)==len(set(ids)),
                 verified_failures=s['verified_failure_events'],inconclusive=s['inconclusive_events'],subsequent=s['subsequent_failure_events'])
        row['pass']=all([row['execution']=='success',row['source_hashes_verified'],row['ac_source_median_residual_V']<1000.,dc_error<1000.,all(segment['pass'] for segment,_ in segments),row['gate_event_window_max_error']<.1,row['unique_firing_event_ids'],s['physical_consistency']=='pass'])
        rows.append(row)
    b=np.load(ROOT/'results/processed/CF-00/signals.npz');t=b['time'];steady=t>.5
    events=json.loads((ROOT/'results/processed/CF-00/events.json').read_text())
    firing=[];widths=[]
    for k in range(1,7):
        g=b[f'G{k}'];r=np.flatnonzero(np.diff(g)>.5)+1;falls=np.flatnonzero(np.diff(g)<-.5)+1
        firing.extend((t[j],k) for j in r if t[j]>.5)
        widths.extend((t[next(q for q in falls if q>j)]-t[j])*50*360 for j in r if .5<t[j]<.57)
    firing.sort();seq=all(b[1]==a[1]%6+1 for a,b in zip(firing,firing[1:]))
    cycle=[float(np.mean(b['Idc_meas'][(t>=lo)&(t<lo+.02)])) for lo in np.arange(.50,.58,.02)]
    baseline=dict(mean_idc_A=float(np.mean(b['Idc_meas'][steady])),mean_vdc_V=float(np.mean(b['Vdc_meas'][steady])),
                  mean_pdc_W=float(np.mean(b['Pdc_to_bridge'][steady])),mean_pac_W=float(np.mean(b['Pac_to_grid'][steady])),
                  peak_to_peak_current_fraction=float(np.ptp(b['Idc_meas'][steady])/np.mean(b['Idc_meas'][steady])),
                  cycle_mean_drift_fraction=(max(cycle)-min(cycle))/np.mean(cycle),
                  firing_sequence_correct=seq,gate_width_deg_min=min(widths),gate_width_deg_max=max(widths),
                  mean_overlap_deg=float(np.mean([e['overlap_deg'] for e in events if e['time_s']>.5])),
                  min_gamma_deg=min(e['gamma_deg'] for e in events if e['time_s']>.5))
    baseline['pass']=bool(seq and baseline['cycle_mean_drift_fraction']<.005 and baseline['mean_pac_W']>1e8 and baseline['mean_pdc_W']>1e8 and baseline['mean_vdc_V']<0 and baseline['min_gamma_deg']>20 and 5<baseline['mean_overlap_deg']<20)
    sensitivity=[]
    for original,refined in [('CF-00','NUM-BASE-5US'),('CF-02','NUM-SAG-5US')]:
        a=json.loads((ROOT/f'results/processed/{original}/summary.json').read_text());b=json.loads((ROOT/f'results/processed/{refined}/summary.json').read_text())
        ea=json.loads((ROOT/f'results/processed/{original}/events.json').read_text());eb=json.loads((ROOT/f'results/processed/{refined}/events.json').read_text())
        fa=next((e for e in ea if e['verified_failure']),None);fb=next((e for e in eb if e['verified_failure']),None)
        sensitivity.append(dict(original=original,refined=refined,peak_current_relative_change=(b['peak_dc_current_A']/a['peak_dc_current_A']-1),
                                failure_count_10us=a['verified_failure_events'],failure_count_5us=b['verified_failure_events'],
                                min_gamma_difference_deg=b['min_valid_gamma_deg']-a['min_valid_gamma_deg'],
                                first_failure_time_difference_s=None if fa is None or fb is None else fb['failure_time_s']-fa['failure_time_s']))
    out=dict(baseline=baseline,cases=rows,numerical_sensitivity=sensitivity,total_executed=len(rows),total_verified_failure_attempts=sum(r['verified_failures'] for r in rows),
             pass_all=bool(baseline['pass'] and all(r['pass'] for r in rows)),scope='Audits data integrity, source profiles, KCL, baseline operation and two time steps; not validation of a complete HVDC control/protection design.')
    dest=ROOT/'results/summary';dest.mkdir(parents=True,exist_ok=True);(dest/'engineering_audit.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2));return out

if __name__=='__main__':
    result=audit()
    if not result['pass_all']:raise SystemExit('Engineering audit failed')
