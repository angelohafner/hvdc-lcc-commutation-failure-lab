"""Conservative valve-level classification, independent of DC voltage alarms."""
import numpy as np

PHASE={1:'A',3:'B',5:'C',4:'A',6:'B',2:'C'}

def first_sustained(mask, samples=3):
    if len(mask)<samples:return None
    indices=np.flatnonzero(np.convolve(np.asarray(mask,dtype=int),np.ones(samples,dtype=int),'valid')==samples)
    return int(indices[0]) if len(indices) else None

def classify_transfer(t,outgoing,incoming,v_out,comm_voltage,idc,frequency=50.,recovery_s=.0002,outgoing_gate=None):
    """Classify one firing attempt; inputs are seconds, amperes and volts.

    The supplied interval ends before the next firing in the same valve group.
    It must not contain a new firing command to the outgoing valve.
    """
    e=dict(classification='inconclusive',verified_failure=False,gamma_deg=None,
           overlap_deg=None,current_completion_s=None,reverse_bias_end_s=None,
           failure_time_s=None,evidence=[])
    values=[np.asarray(x) for x in [t,outgoing,incoming,v_out,comm_voltage,idc]]
    if len(t)<8 or any(len(x)!=len(t) or not np.all(np.isfinite(x)) for x in values):
        e['evidence']=['Missing or non-finite valve-level evidence'];return e
    t,outgoing,incoming,v_out,comm_voltage,idc=values
    threshold=max(10.,.02*float(np.median(abs(idc))))
    high=max(50.,.1*float(np.median(abs(idc))))
    e.update(current_threshold_A=threshold,outgoing_at_gate_A=float(outgoing[0]),
             incoming_at_gate_A=float(incoming[0]),incoming_peak_A=float(np.max(incoming)),
             incoming_rise_A=float(np.max(incoming)-incoming[0]))
    if outgoing[0]<high:
        e['evidence']=['No established outgoing-valve current at the firing instant'];return e
    rise=first_sustained(incoming>incoming[0]+high)
    if incoming[0]>=high or rise is None:
        e['evidence']=['Incoming current was already established or no sustained post-gate rise was observed; a new transfer is not established'];return e
    e['incoming_rise_time_s']=float(t[rise])
    zero=first_sustained(outgoing<threshold)
    if zero is not None:
        e['current_threshold_crossing_s']=float(t[zero])
        back=first_sustained(outgoing[zero+3:]>high)
        if back is not None:
            j=zero+3+back
            if outgoing_gate is not None and np.any(np.diff(np.asarray(outgoing_gate)[:j+1])>.5):
                e['evidence']=['Outgoing valve received a new gate command; resumed-current evidence is ambiguous'];return e
            reverse=first_sustained(v_out[zero:j] < -500.)
            if reverse is None:
                e['evidence']=['Current dipped below its threshold but no reverse-blocking interval was observed before it rose again'];return e
            # Resumed positive current plus a low conducting voltage, without a new gate.
            if np.max(incoming[:j])>high and abs(v_out[j])<1000.:
                e.update(classification='resumed_conduction',verified_failure=True,
                         failure_time_s=float(t[j]),current_completion_s=float(t[zero+reverse]),
                         reverse_bias_start_s=float(t[zero+reverse]),
                         overlap_deg=float((t[zero+reverse]-t[0])*frequency*360.))
                e['evidence']=['Outgoing current reached its off threshold, sustained reverse voltage, and then resumed without a new gate',
                               'Incoming current rose and outgoing valve voltage returned to a conducting value']
                return e
            e['evidence']=['Outgoing current returned, but its voltage did not establish resumed conduction; contradictory evidence cannot establish successful extinction']
            return e
        reverse=first_sustained(v_out[zero:] < -500.)
        if reverse is None:
            e['evidence']=['Current crossed its off threshold but sustained reverse voltage was not established'];return e
        rs=zero+reverse
        e['current_completion_s']=float(t[rs]);e['overlap_deg']=float((t[rs]-t[0])*frequency*360.)
        forward=first_sustained(v_out[rs:]>500.)
        if forward is None:
            e['evidence']=['Reverse-bias interval extends beyond the inspected window'];return e
        end=rs+forward
        e['reverse_bias_start_s']=float(t[rs]);e['reverse_bias_end_s']=float(t[end])
        e['gamma_deg']=float((t[end]-t[rs])*frequency*360.)
        if np.max(incoming[zero:])<high:
            e['evidence']=['Outgoing current disappeared without evidence of incoming conduction'];return e
        e['classification']='reduced_margin' if e['gamma_deg']<15. else 'normal'
        e['evidence']=['Outgoing current extinguished; incoming valve carried current',
                       'Outgoing valve sustained reverse voltage and did not resume conduction in the observation interval']
        e['recovery_time_margin_s']=float(t[end]-t[rs]-recovery_s)
        return e
    positive=first_sustained(comm_voltage>1000.)
    reversal=None
    if positive is not None:
        search=max(positive+3,rise);negative=first_sustained(comm_voltage[search:] < -1000.)
        if negative is not None:reversal=search+negative
    if reversal is not None and np.max(incoming)>high and outgoing[reversal]>high and abs(v_out[reversal])<1000.:
        e.update(classification='unsuccessful_transfer',verified_failure=True,failure_time_s=float(t[reversal]))
        e['evidence']=['Gate applied and incoming current rose, but outgoing current never extinguished',
                       'Measured PCC commutation voltage reversed while the outgoing valve remained conducting']
    else:e['evidence']=['Current transfer was not completed, but the available evidence is insufficient for a verified failure']
    return e

def detect_events(t,d,parameters,analysis_start=.22):
    events=[];f=parameters['frequency_hz']
    gates={k:np.flatnonzero((d[f'G{k}'][1:]>.5)&(d[f'G{k}'][:-1]<=.5))+1 for k in range(1,7)}
    for incoming in range(1,7):
        rises=gates[incoming]
        group=[1,3,5] if incoming%2 else [2,4,6]
        group_rises=np.unique(np.concatenate([gates[k] for k in group]))
        expected=(incoming-3)%6+1
        for i in rises:
            later=group_rises[group_rises>i]
            if t[i]<analysis_start or not len(later):continue
            others=[k for k in group if k!=incoming]
            outgoing=max(others,key=lambda k:d[f'IT{k}'][max(0,i-2)])
            stop=int(later[0])
            sl=slice(i,stop)
            polarity=1 if incoming%2 else -1
            u=polarity*(d['VPCC'+PHASE[incoming]][sl]-d['VPCC'+PHASE[outgoing]][sl])
            e=classify_transfer(t[sl],d[f'IT{outgoing}'][sl],d[f'IT{incoming}'][sl],d[f'VT{outgoing}'][sl],u,d['Idc_meas'][sl],
                                frequency=f,recovery_s=parameters['recovery_us']*1e-6,outgoing_gate=d[f'G{outgoing}'][sl])
            if sum(i in gates[k] for k in group)>1:
                e.update(classification='inconclusive',verified_failure=False,gamma_deg=None,overlap_deg=None,current_completion_s=None,
                         evidence=['Simultaneous gate edges in one valve group do not establish an isolated transfer'])
            e.update(time_s=float(t[i]),incoming=f'T{incoming}',outgoing=f'T{outgoing}',
                     expected_outgoing=f'T{expected}',abnormal_sequence=outgoing!=expected,
                     window_end_s=float(t[stop-1]),next_group_gate_s=float(t[stop]))
            events.append(e)
    events.sort(key=lambda e:e['time_s'])
    for j,e in enumerate(events):e['event_id']=f'E{j+1:03d}'
    return events

def characterize_sequence(events,clearing_time):
    """Require six consecutive successful attempts after clearing before recurrence.

    This is a deliberately stricter operational definition of subsequent failure
    than merely occurring later than fault clearing. Inconclusive attempts break
    the consecutive-success count, but do not erase an already observed recovery.
    Recovery must persist for the remaining record to be
    reported as stable recovery.
    """
    post=[e for e in events if e['time_s']>=clearing_time]
    consecutive=0;recovered=False;subsequent=0;stable_start=None;intervals=[]
    for e in post:
        if e['classification'] in ['normal','reduced_margin']:
            if consecutive==0:stable_start=e['time_s']
            consecutive+=1
            if consecutive==6:
                if not recovered:intervals.append(dict(start_s=stable_start,established_s=e['time_s'],next_failure_s=None))
                recovered=True
        else:
            if e['verified_failure'] and recovered:
                subsequent+=1;e['subsequent_after_recovery']=True
                intervals[-1]['next_failure_s']=e['time_s'];recovered=False
            consecutive=0;stable_start=None
    return dict(post_clearing_failure_events=sum(e['verified_failure'] for e in post),
                subsequent_failure_events=subsequent,
                recovery_intervals=intervals,
                stable_recovery_start_s=stable_start if consecutive>=6 else None,
                stable_recovery_delay_s=max(0.,stable_start-clearing_time) if consecutive>=6 else None,
                recovery_criterion='Six consecutive successful attempts after clearing, maintained to record end')
