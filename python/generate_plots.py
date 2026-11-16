"""Create engineering figures directly from validated native-data arrays."""
from pathlib import Path
import argparse,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from detect_failures import PHASE

ROOT=Path(__file__).resolve().parents[1]
COLORS=['#1265b0','#c14b2d','#14816f','#9361b3','#ae7418','#586875']
plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.2,'figure.facecolor':'white','savefig.facecolor':'white'})

def save(fig,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    for ext in ['png','svg']:fig.savefig(path.with_suffix('.'+ext),dpi=150,bbox_inches='tight')
    plt.close(fig)

def plots(case):
    folder=ROOT/'results/processed'/case
    z=np.load(folder/'signals.npz');t=z['time'];meta=json.loads((folder/'metadata.json').read_text())
    events=json.loads((folder/'events.json').read_text());f=meta['parameters']['frequency_hz']
    dest=ROOT/'figures/waveforms'/case
    fig,ax=plt.subplots(4,1,figsize=(12,10),sharex=True)
    for phase,col in zip('ABC',COLORS):ax[0].plot(t,z['VPCC'+phase]/1000,label=phase,color=col,lw=.8)
    ax[0].set_ylabel('PCC voltage (kV)');ax[0].legend(ncol=3,loc='upper right')
    ax[1].plot(t,z['Vdc_meas']/1000,color=COLORS[0]);ax[1].set_ylabel('Bridge DC voltage (kV)')
    ax[2].plot(t,z['Idc_meas']/1000,color=COLORS[1]);ax[2].set_ylabel('DC current (kA)')
    ax[3].plot(t,z['Pdc_to_bridge']/1e6,label='DC into bridge',lw=1)
    ax[3].plot(t,z['Pac_to_grid']/1e6,label='AC into grid',lw=.8,alpha=.7);ax[3].set_ylabel('Power (MW)');ax[3].legend()
    ax[3].set_xlabel('Time (s)')
    for a in ax:
        p=meta['parameters'];a.axvspan(p['fault_start_s'],p['fault_start_s']+p['fault_duration_s'],color='#d79a30',alpha=.12)
    fig.suptitle(case+' | '+meta['parameters']['title']+' | Actual PSCAD output')
    save(fig,dest/'overview')
    fig,ax=plt.subplots(3,1,figsize=(12,8),sharex=True)
    for k,col in zip(range(1,7),COLORS):
        ax[0].plot(t,z[f'IT{k}']/1000,label=f'T{k}',color=col,lw=.8)
        ax[1].plot(t,z[f'VT{k}']/1000,label=f'T{k}',color=col,lw=.7)
        ax[2].plot(t,z[f'G{k}']+1.4*(6-k),color=col,lw=.7)
    ax[0].set_ylabel('Valve current (kA)');ax[0].legend(ncol=6)
    ax[1].set_ylabel('Anode–cathode (kV)');ax[2].set_ylabel('Gate commands (offset)');ax[2].set_xlabel('Time (s)')
    ax[2].set_xlim(.28,.42);fig.suptitle(case+' | Six individual thyristors')
    save(fig,dest/'valves_and_gates')
    selected=[e for e in events if e['verified_failure']][:1]
    if not selected:selected=events[-10:-9]
    if selected:detail(case,z,selected[0],dest/'selected_commutation')
    if events:
        fig,ax=plt.subplots(figsize=(12,4))
        ax.plot(t,z['AlphaRef'],label='Firing reference alpha',color=COLORS[0]);ax.plot(t,180-z['AlphaRef'],label='Advance reference beta',color=COLORS[3])
        for key,label,col in [('gamma_deg','Measured gamma: valid events',COLORS[2]),('overlap_deg','Measured overlap: completed transfers',COLORS[4])]:
            valid=[e for e in events if e[key] is not None];ax.scatter([e['time_s'] for e in valid],[e[key] for e in valid],s=10,label=label,color=col)
        ax.set(xlabel='Time (s)',ylabel='Angle (degrees)',xlim=(.2,t[-1]));ax.legend(ncol=2,fontsize=8);fig.suptitle(case+' | References and measured event angles')
        save(fig,dest/'angles')
        fig,ax=plt.subplots(figsize=(12,4))
        for cl,col in [('normal',COLORS[0]),('reduced_margin',COLORS[4]),('unsuccessful_transfer',COLORS[1]),('resumed_conduction',COLORS[3]),('inconclusive','#7d868b')]:
            es=[e for e in events if e['classification']==cl]
            if es:ax.scatter([e['time_s'] for e in es],[int(e['incoming'][1:]) for e in es],s=25,label=cl.replace('_',' '),color=col)
        ax.set(xlabel='Firing time (s)',ylabel='Incoming valve',yticks=range(1,7));ax.legend(loc='upper left',bbox_to_anchor=(1,1));fig.suptitle(case+' | One event record per firing attempt')
        save(fig,dest/'event_timeline')

def detail(case,z,e,path):
    t=z['time'];i=int(e['incoming'][1:]);o=int(e['outgoing'][1:])
    s=e['time_s'];mask=(t>=s-.001)&(t<=e['window_end_s']+.0003);tm=(t[mask]-s)*1000
    fig,ax=plt.subplots(4,1,figsize=(11,9),sharex=True)
    ax[0].plot(tm,z[f'IT{o}'][mask]/1000,label=f'T{o}: outgoing',color=COLORS[1],lw=2)
    ax[0].plot(tm,z[f'IT{i}'][mask]/1000,label=f'T{i}: incoming',color=COLORS[0],lw=2)
    ax[0].set_ylabel('Valve current (kA)');ax[0].legend(loc='best')
    ax[1].plot(tm,z[f'VT{o}'][mask]/1000,label=f'T{o}: anode–cathode',color=COLORS[1]);ax[1].axhline(0,color='black',lw=.6);ax[1].set_ylabel('Valve voltage (kV)');ax[1].legend()
    u=(1 if i%2 else -1)*(z['VPCC'+PHASE[i]]-z['VPCC'+PHASE[o]])
    ax[2].plot(tm,u[mask]/1000,color=COLORS[2]);ax[2].axhline(0,color='black',lw=.6);ax[2].set_ylabel('PCC commutation\nvoltage (kV)')
    ax[3].step(tm,z[f'G{i}'][mask],where='post',label=f'T{i}: gate',color=COLORS[0]);ax[3].step(tm,z[f'G{o}'][mask],where='post',label=f'T{o}: gate',color=COLORS[1],ls='--');ax[3].set(ylim=(-.15,1.2),ylabel='Gate command',xlabel=f'Time relative to firing at {s:.5f} s (ms)');ax[3].legend()
    for a in ax:
        a.axvline(0,color='#343c46',ls=':',lw=1)
        if e.get('current_completion_s') is not None:a.axvline((e['current_completion_s']-s)*1000,color='#14816f',ls='--',lw=1)
        if e.get('failure_time_s') is not None:a.axvline((e['failure_time_s']-s)*1000,color='#c14b2d',ls='--',lw=1)
    fig.suptitle(f"{case} / {e['event_id']}: {e['outgoing']} to {e['incoming']} | {e['classification'].replace('_',' ')}\nActual PSCAD samples; dashed marker = current extinction or verified failure evidence")
    save(fig,path)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('cases',nargs='*',default=['CF-00','CF-02']);args=ap.parse_args()
    for case in args.cases:plots(case)
