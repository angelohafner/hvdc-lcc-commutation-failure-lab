"""Run real PSCAD cases; archive hashes, native files, and execution receipts."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, shutil, math
import xml.etree.ElementTree as ET
import mhi.pscad
from build_model import ROOT, NOMINAL

CASES={
 'CF-00':dict(title='Normal thyristor commutation'),
 'CF-01':dict(title='Reduced extinction margin without failure',alpha_deg=150.,alpha_event_deg=150.,dc_voltage_v=131200.),
 'CF-02':dict(title='Balanced three-phase voltage sag',sag_pu=0.5),
 'CF-03':dict(title='Single-line-to-ground fault',fault_type=1),
 'CF-04':dict(title='Line-to-line fault',fault_type=2),
 'CF-05':dict(title='Double-line-to-ground fault',fault_type=3),
 'CF-06':dict(title='Severe three-phase short circuit',fault_type=4,fault_resistance_ohm=0.2),
 'CF-07':dict(title='AC voltage phase-angle jump',phase_jump_deg=-25.),
 'CF-08':dict(title='Sudden increase in DC source driving voltage',dc_step_pu=1.3),
 'CF-09':dict(title='Insufficient extinction margin',alpha_event_deg=168.),
 'CF-10':dict(title='Weak AC grid',grid_inductance_h=0.06,sag_pu=0.8),
 'CF-11':dict(title='Fifth harmonic commutation-voltage distortion',harmonic_pu=0.25),
 'CF-12':dict(title='Repeated failures during one voltage sag',sag_pu=0.3,fault_duration_s=0.12),
 'CF-13':dict(title='Recovery after one AC disturbance',sag_pu=0.35,fault_duration_s=0.08),
 'CF-14':dict(title='Persistent severe AC disturbance',sag_pu=0.15,fault_duration_s=0.25,duration_s=0.7),
}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def setparam(node,key,value):
    pl=node.find('paramlist')
    if pl is None:pl=ET.SubElement(node,'paramlist')
    p=pl.find(f"param[@name='{key}']")
    if p is None:p=ET.SubElement(pl,'param',name=key)
    p.set('value',str(value))

def prepare(case,overrides=None):
    spec={**NOMINAL,**CASES.get(case,{}),**(overrides or {})}
    spec.setdefault('title',case)
    # Optional operating-point references are feedforward estimates, not feedback controls.
    if 'scr' in spec:
        z=spec['ac_voltage_v']**2/(150e6*spec['scr'])
        if z<=spec['grid_resistance_ohm']:raise ValueError('Requested SCR is incompatible with grid resistance')
        spec['grid_inductance_h']=math.sqrt(z*z-spec['grid_resistance_ohm']**2)/(2*math.pi*spec['frequency_hz'])
    if 'gamma_reference_deg' in spec:
        current=spec.get('dc_current_reference_a',1300.)
        x=2*math.pi*spec['frequency_hz']*(spec['grid_inductance_h']+spec['commutation_h'])
        c=2*x*current/(math.sqrt(2)*spec['ac_voltage_v'])-math.cos(math.radians(spec['gamma_reference_deg']))
        if not -1<c<0:raise ValueError('Requested gamma/current is outside this inverter feedforward domain')
        spec['alpha_deg']=math.degrees(math.acos(c));spec['alpha_event_deg']=spec['alpha_deg']
        spec.setdefault('dc_current_reference_a',current)
    if 'dc_current_reference_a' in spec:
        x=2*math.pi*spec['frequency_hz']*(spec['grid_inductance_h']+spec['commutation_h'])
        spec['dc_voltage_v']=(-3*math.sqrt(2)/math.pi*spec['ac_voltage_v']*math.cos(math.radians(spec['alpha_deg']))
                              +(3*x/math.pi+spec['dc_resistance_ohm'])*spec['dc_current_reference_a'])
        spec['reference_method']='Balanced sinusoidal feedforward estimate; inspect measured steady state; no current/gamma feedback'
    name='LCC_'+case.replace('-','_')
    template=ROOT/'pscad/inverter_6_pulse/lcc_inverter.pscx'
    root=ET.fromstring(template.read_text().replace('lcc_inverter',name))
    ids=json.loads((template.parent/'component_ids.json').read_text())
    def component(i):return root.find(f".//User[@id='{i}']")
    for k in NOMINAL:setparam(component(ids['controller']),k,spec[k])
    for i in ids['valves'].values():setparam(component(i),'TEXT',f"{spec['recovery_us']} [us]")
    for phase in 'ABC':
        setparam(component(ids['commutation'][phase]),'L',f"{spec['commutation_h']} [H]")
        setparam(component(ids['grid'][phase]['l']),'L',f"{spec['grid_inductance_h']} [H]")
        setparam(component(ids['grid'][phase]['r']),'R',f"{spec['grid_resistance_ohm']} [ohm]")
    for i in ids['faults'].values():setparam(component(i),'ROn',f"{spec['fault_resistance_ohm']} [ohm]")
    setparam(component(ids['rdc']),'R',f"{spec['dc_resistance_ohm']} [ohm]")
    setparam(component(ids['ldc']),'L',f"{spec['smoothing_h']} [H]")
    settings=root.find("./paramlist[@name='Settings']")
    for k,v in dict(time_duration=spec['duration_s'],time_step=spec['time_step_us'],sample_step=spec['time_step_us'],
                    output_filename=name+'.out',description=spec['title']).items():
        settings.find(f"param[@name='{k}']").set('value',str(v))
    for seg in root.findall('.//segment'):
        if seg.text and '#LOCAL' in seg.text:
            lines=[]
            for line in seg.text.splitlines():
                if line.startswith('#LOCAL') and ',' in line:
                    _,typ,variables=line.split(' ',2)
                    lines.extend(f'#LOCAL {typ} {s.strip()}' for s in variables.split(','))
                else:lines.append(line)
            seg.text='\n'.join(lines)
    path=ROOT/'pscad/simulation_cases'/f'{name}.pscx';path.parent.mkdir(exist_ok=True)
    ET.indent(root);ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
    return path,spec

def run(app,case,overrides=None):
    dest=ROOT/'results/raw'/case
    if dest.exists():raise FileExistsError(f'{case} already has evidence; choose a distinct run ID')
    name='LCC_'+case.replace('-','_')
    if name in app.project_names():app.project(name).unload()
    path,spec=prepare(case,overrides)
    app.load(str(path));p=app.project(name);p.parameters(PlotType='OUT');p.save()
    dest.mkdir(parents=True)
    started=datetime.now(timezone.utc)
    receipt=dict(case_id=case,parameters=spec,project=path.relative_to(ROOT).as_posix(),project_sha256=sha(path),
                 pscad_version=app.version,compiler=app.settings()['fortran_version'],licensed=app.licensed(),
                 start_utc=started.isoformat(),execution_status='started')
    log=dest/'receipt.json';log.write_text(json.dumps(receipt,indent=2));print('RUN',case,flush=True)
    try:
        p.run()
        messages=[dict(status=m.status,text=m.text) for m in p.messages()]
        (dest/'messages.json').write_text(json.dumps(messages,indent=2))
        errors=[m for m in messages if m['status']=='error']
        build=Path(p.temp_folder)
        files=list(build.glob(name+'_*.out'))+[build/(name+'.inf')]
        if errors:raise RuntimeError(errors)
        if len(files)<5 or not all(f.is_file() for f in files):raise RuntimeError('Native output files are missing')
        if not all(f.stat().st_mtime>=started.timestamp()-2 for f in files):raise RuntimeError('Stale native output')
        for f in files:shutil.copy2(f,dest/f.name)
        shutil.copy2(path,dest/path.name)
        receipt.update(execution_status='success',errors=[],warnings=[m for m in messages if m['status']=='warning'],
                       output_sha256={f.name:sha(f) for f in files})
    except Exception as exc:
        receipt.update(execution_status='failed',errors=[str(exc)]);raise
    finally:
        receipt['finish_utc']=datetime.now(timezone.utc).isoformat();log.write_text(json.dumps(receipt,indent=2))
    print('EXECUTED',case,flush=True);return dest

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=0)
    ap.add_argument('--cases',nargs='+',default=['CF-00']);ap.add_argument('--overrides',default='{}')
    args=ap.parse_args();a=mhi.pscad.connect(port=args.port);assert a.licensed()
    for case in args.cases:run(a,case,json.loads(args.overrides))
