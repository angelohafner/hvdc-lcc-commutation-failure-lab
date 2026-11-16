"""Matched scientific comparisons and unrounded selected native samples."""
import csv,json,shutil
import numpy as np
import matplotlib.pyplot as plt
from generate_plots import ROOT,COLORS,save,detail

def load(case):
    p=ROOT/'results/processed'/case
    return np.load(p/'signals.npz'),json.loads((p/'events.json').read_text()),json.loads((p/'summary.json').read_text())

def build():
    dest=ROOT/'figures/comparisons'
    for name,cases in [('mitigation',['CF-02','MIT-ANGLE','MIT-DC']),('recovery',['CF-13-R2','REC-NOMINAL'])]:
        fig,ax=plt.subplots(4,1,figsize=(12,10),sharex=True)
        for case,col in zip(cases,COLORS):
            z,ev,s=load(case);t=z['time'];mask=t>=.25
            for a,key,scale,label in zip(ax,['Idc_meas','Vdc_meas','Pac_to_grid'],[.001,.001,1e-6],['DC current (kA)','DC voltage (kV)','AC power (MW)']):
                a.plot(t[mask],z[key][mask]*scale,label=case,color=col,lw=.8,alpha=.85);a.set_ylabel(label)
            failed=[e for e in ev if e['verified_failure']];ax[3].scatter([e['time_s'] for e in failed],[cases.index(case)+1]*len(failed),s=13,color=col,label=case)
        for a in ax:a.axvspan(.3,.38,color='#e2ae46',alpha=.15)
        ax[0].legend();ax[3].set(yticks=range(1,len(cases)+1),yticklabels=cases,ylabel='Verified attempts',xlabel='Time (s)')
        fig.suptitle(('Matched 50% sag | DC reduction trades power for current limitation' if name=='mitigation' else 'One AC sag | Prescribed DC restoration with and without overshoot')+'\nActual PSCAD recordings; independent runs, common time axis')
        save(fig,dest/name)
    fig,ax=plt.subplots(3,2,figsize=(12,9),sharex=True,sharey='row')
    for col,case in enumerate(['CF-00','CF-02']):
        z,ev,s=load(case);e=next(e for e in ev if e['incoming']=='T5' and (e['verified_failure'] if col else e['time_s']>.5));t=z['time'];m=(t>=e['time_s']-.001)&(t<e['time_s']+.0067);x=(t[m]-e['time_s'])*1000
        for k,color in [(3,COLORS[1]),(5,COLORS[0])]:ax[0,col].plot(x,z[f'IT{k}'][m]/1000,label=f'T{k}',color=color,lw=1.5)
        ax[1,col].plot(x,z['VT3'][m]/1000,color=COLORS[1],label='T3 anode-cathode')
        ax[2,col].plot(x,(z['VPCCC'][m]-z['VPCCB'][m])/1000,color=COLORS[2],label='PCC C minus B')
        ax[0,col].set_title(case+' / '+e['event_id']+' / '+e['classification'].replace('_',' '));ax[0,col].legend()
        for a in ax[:,col]:a.axvline(0,color='#526d7e',ls=':',lw=1)
        ax[2,col].set_xlabel('Time from incoming T5 firing (ms)')
    for a,y in zip(ax[:,0],['Current (kA)','Valve voltage (kV)','Driving voltage (kV)']):a.set_ylabel(y)
    fig.suptitle('Same valve pair, common scales | Successful versus failed transfer');save(fig,dest/'normal_vs_failed')
    z,ev,s=load('CF-13-R2');e=next(e for e in ev if e.get('subsequent_after_recovery'))
    detail('CF-13-R2',z,e,dest/'subsequent_detail')
    z,ev,s=load('CF-06');e=next(e for e in ev if e['classification']=='resumed_conduction')
    detail('CF-06',z,e,dest/'resumed_conduction')
    samples=ROOT/'results/validated_samples';samples.mkdir(exist_ok=True)
    for case in ['CF-00','CF-01','CF-02','CF-06','CF-07','CF-13-R2','MIT-DC']:
        z,ev,s=load(case);e=next((e for e in ev if e.get('subsequent_after_recovery')),None) or next((e for e in ev if e['verified_failure']),None) or next(e for e in ev if e['time_s']>.5)
        if case=='CF-06':e=next(e for e in ev if e['classification']=='resumed_conduction')
        m=(z['time']>=e['time_s']-.001)&(z['time']<=e['time_s']+.0067);fields=['time','Idc_meas','Vdc_meas']+[f'{x}{k}' for x in ['IT','VT','G'] for k in range(1,7)]+['VPCCA','VPCCB','VPCCC']
        np.savetxt(samples/(case+'_event.csv'),np.column_stack([z[k][m] for k in fields]),delimiter=',',header=','.join(fields),comments='',fmt='%.15g')
        (samples/(case+'_event.json')).write_text(json.dumps(e,indent=2))
    web=ROOT/'docs/assets/images';web.mkdir(parents=True,exist_ok=True)
    for f in dest.glob('*.png'):shutil.copy2(f,web/f.name)
    for case in ['CF-00','CF-02','CF-12','CF-13-R2']:
        for name in ['selected_commutation','event_timeline','angles']:
            f=ROOT/f'figures/waveforms/{case}/{name}.png'
            if f.exists():shutil.copy2(f,web/f'{case}_{name}.png')

if __name__=='__main__':build()
