"""Construct an original inverter using references to installed PSCAD components."""
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET
import mhi.pscad

ROOT = Path(__file__).resolve().parents[1]
NOMINAL = dict(frequency_hz=50., ac_voltage_v=100000., dc_voltage_v=118000.,
               dc_resistance_ohm=5., smoothing_h=0.5, grid_resistance_ohm=0.3,
               grid_inductance_h=0.01, commutation_h=0.01, alpha_deg=140.,
               recovery_us=200., fault_start_s=0.3, fault_duration_s=0.08,
               sag_pu=1., phase_jump_deg=0., dc_step_pu=1., harmonic_pu=0.,
               fault_type=0, fault_resistance_ohm=2., alpha_event_deg=140.,
               dc_reduce_pu=1., recovery_dc_pu=1., recovery_hold_s=0.,
               restore_overshoot_pu=0., restore_decay_s=.05, restore_rise_s=0.,
               duration_s=0.6, time_step_us=10.)


def controller_definition():
    """Original source profiles and a grid-referenced six-pulse firing clock."""
    d=ET.Element('Definition',classid='UserCmpDefn',name='LabController')
    pl=ET.SubElement(d,'paramlist')
    ET.SubElement(pl,'param',name='Description',value='Original LCC source profiles and firing clock')
    form=ET.SubElement(d,'form',name='Lab Controller',w='600',h='600')
    cat=ET.SubElement(form,'category',name='Configuration')
    ET.SubElement(cat,'cond').text='true'
    outputs={**{f'G{k}':'Integer' for k in range(1,7)},
             **{k:'Real' for k in ['EA','EB','EC','EDC','AlphaRef','FaultActive','SagApplied']},
             **{k:'Integer' for k in ['FA','FB','FC','FAB']}}
    for name,value in NOMINAL.items():
        p=ET.SubElement(cat,'parameter',type='Real',name=name,desc=name.replace('_',' '),
                        content_type='Constant',min='-1E30',max='1E30',unit='',intent='Input',dim='1')
        ET.SubElement(p,'value').text=str(value)
        ET.SubElement(p,'cond',type='Enable').text='true'
    for name in outputs:
        p=ET.SubElement(cat,'parameter',type='Text',name=name,desc='Output '+name,allowemptystr='false')
        ET.SubElement(p,'value').text=name
        ET.SubElement(p,'cond',type='Enable').text='true'
    graphics=ET.SubElement(d,'graphics',size='4')
    gp=ET.SubElement(graphics,'paramlist')
    ET.SubElement(gp,'param',name='show_border',value='0')
    script=ET.SubElement(d,'script')
    lines=[*[f'#LOCAL REAL {v}' for v in ['TH','SAG','EVENT','ALPHA','PHASE','DCFACTOR','RAMP','VA','VB','VC','VD','HARM','AFTER']],
           *[f'#LOCAL INTEGER {v}' for v in ['GA','GB','GC','GAB']],
           '      TH = TIME * 360.0 * $frequency_hz',
           '      EVENT = 0.0',
           '      IF (TIME .GE. $fault_start_s .AND.',
           '     + TIME .LT. ($fault_start_s+$fault_duration_s)) EVENT=1.0',
           '      SAG = 1.0 + EVENT * ($sag_pu-1.0)',
           '      PHASE = EVENT * $phase_jump_deg',
           '      ALPHA = $alpha_deg + EVENT*($alpha_event_deg-$alpha_deg)',
           '      DCFACTOR=1.0+EVENT*($dc_step_pu*$dc_reduce_pu-1.0)',
           '      AFTER=TIME-($fault_start_s+$fault_duration_s)',
           '      IF (AFTER.GE.0.0 .AND. $recovery_hold_s.GT.0.0) THEN',
           '        IF (AFTER.LT.$recovery_hold_s) THEN',
           '          DCFACTOR=$recovery_dc_pu',
           '        ELSE',
           '          DCFACTOR=1.0+$restore_overshoot_pu',
           '     +      *EXP(-(AFTER-$recovery_hold_s)/$restore_decay_s)',
           '          IF ($restore_rise_s.GT.0.0) DCFACTOR=1.0',
           '     +      +(DCFACTOR-1.0)*(1.0',
           '     +      -EXP(-(AFTER-$recovery_hold_s)/$restore_rise_s))',
           '        ENDIF',
           '      ENDIF',
           '      RAMP=MIN(1.0, MAX(0.0,(TIME-0.02)/0.08))',
           '      HARM=EVENT*$harmonic_pu',
           '      VA=$ac_voltage_v/1000.0*SQRT(2.0/3.0)',
           '     + *(SAG*SIN((TH+PHASE)*PI_BY180)',
           '     + + HARM*SIN(5.0*TH*PI_BY180))',
           '      VB=$ac_voltage_v/1000.0*SQRT(2.0/3.0)',
           '     + *(SAG*SIN((TH-120.0+PHASE)*PI_BY180)',
           '     + + HARM*SIN(5.0*(TH-120.0)*PI_BY180))',
           '      VC=$ac_voltage_v/1000.0*SQRT(2.0/3.0)',
           '     + *(SAG*SIN((TH+120.0+PHASE)*PI_BY180)',
           '     + + HARM*SIN(5.0*(TH+120.0)*PI_BY180))',
           '      VD=-$dc_voltage_v/1000.0*DCFACTOR*RAMP',
           '      GA=0', '      GB=0', '      GC=0', '      GAB=0',
           '      IF (EVENT .GT. 0.5) THEN',
           '        IF (NINT($fault_type).EQ.1) GA=1',
           '        IF (NINT($fault_type).EQ.2) GAB=1',
           '        IF (NINT($fault_type).EQ.3) THEN',
           '          GB=1', '          GC=1', '        ENDIF',
           '        IF (NINT($fault_type).EQ.4) THEN',
           '          GA=1', '          GB=1', '          GC=1', '        ENDIF',
           '      ENDIF']
    for k in range(1,7):
        lines += [f'#LOCAL INTEGER IG{k}', f'      IG{k}=0',
                  f'      IF (MODULO(TH-30.0-ALPHA-{(k-1)*60}.0,360.0)',
                  f'     + .LT. 120.0 .AND. TIME.GE.0.02) IG{k}=1',
                  f'#OUTPUT INTEGER G{k} {{IG{k}}}']
    for name,expr in dict(EA='VA',EB='VB',EC='VC',EDC='VD',AlphaRef='ALPHA',
                          FaultActive='EVENT',SagApplied='SAG',FA='GA',FB='GB',FC='GC',FAB='GAB').items():
        lines.append(f'#OUTPUT {outputs[name].upper()} {name} {{{expr}}}')
    ET.SubElement(script,'segment',name='Fortran',classid='CoreSegment').text='\n'.join(lines)
    return d


def build(app):
    dest=ROOT/'pscad/inverter_6_pulse';dest.mkdir(parents=True,exist_ok=True)
    path=dest/'lcc_inverter.pscx'
    if 'lcc_inverter' in app.project_names():
        existing=app.project('lcc_inverter')
        if Path(existing.filename).resolve()!=path.resolve():
            raise RuntimeError('An unrelated project has the same name')
        existing.unload()
    if path.exists():
        # Only replace this generator's project, preserving unrelated workspace projects.
        path.unlink()
    p=app.create_case('lcc_inverter',str(dest));c=p.canvas('Main')
    c.parameters(size='100X100')
    p.parameters(time_duration=NOMINAL['duration_s'],time_step=10.,sample_step=10.,
                 PlotType='OUT',output_filename='lcc_inverter.out',
                 description='Original standalone six-pulse LCC inverter educational study')
    p.create_definition(controller_definition())
    ctrl=c.create_component('lcc_inverter:LabController',8,90)
    ids={'controller':ctrl.iid,'valves':{},'sources':{},'grid':{},'commutation':{},'faults':{}}
    def comp(name,x,y,**kw):return c.create_component('master:'+name,x,y,**kw)
    def point(o,port):
        q=o.ports()[port];return q.x,q.y
    def wire(a,b):
        if a!=b:c.create_wire(a,b)
    def label(name,xy):return comp('datalabel',*xy,Name=name)
    def electric_label(name,xy):return comp('nodelabel',*xy,Name=name)
    def sig(o,port,name):label(name,point(o,port))
    # Every electrical node is joined by named native electrical labels.
    # This avoids ambiguous crossing wires in the model and makes topology auditable.
    for phase,x,upper,lower in [('A',32,1,4),('B',52,3,6),('C',72,5,2)]:
        for k,y,anode,cathode in [(upper,25,phase,'P'),(lower,45,'N',phase)]:
            t=comp('peswitch',x,y,Name=f'T{k}',L=f'T{k}',Type=1,INTR=0,SNUB=0,
                   RON='0.01 [ohm]',ROFF='1e8 [ohm]',TEXT='200 [us]',
                   I=f'IT{k}',V=f'VT{k}',Gamma=f'GammaT{k}',Ton=f'Ton{k}',Toff=f'Toff{k}')
            electric_label(anode,point(t,'DP'));electric_label(cathode,point(t,'DN'))
            sig(t,'APUL',f'G{k}');ids['valves'][str(k)]=t.iid
        lc=comp('inductor',x,60,L='0.01 [H]',Name='Lc_'+phase)
        electric_label(phase,point(lc,'A'));electric_label('BUS_'+phase,point(lc,'B'))
        ids['commutation'][phase]=lc.iid
        r=comp('resistor',x,70,R='0.3 [ohm]',Name='Rg_'+phase)
        electric_label('BUS_'+phase,point(r,'A'));electric_label('RG_'+phase,point(r,'B'))
        lg=comp('inductor',x+6,70,L='0.01 [H]',Name='Lg_'+phase)
        electric_label('RG_'+phase,point(lg,'A'));electric_label('EMF_'+phase,point(lg,'B'))
        ids['grid'][phase]=dict(r=r.iid,l=lg.iid)
        src=comp('source_1',x,80,Name='Grid_'+phase,Type=6,Grnd=1,Spec=0,Cntrl=1,AC=0,Tc='0 [s]',CUR='IG'+phase)
        electric_label('EMF_'+phase,point(src,'NA'));sig(src,'Mag','E'+phase)
        ids['sources'][phase]=src.iid
        for prefix,node,yy in [('VAC',phase,55),('VPCC','BUS_'+phase,65)]:
            v=comp('voltmetergnd',x+10,yy,Name=prefix+phase)
            electric_label(node,point(v,'N1'))
    for k,x,y in [('A',26,110),('B',42,110),('C',58,110),('AB',74,110)]:
        f=comp('fault_sw',x,y,Name='F'+k,ROn='2 [ohm]',ROff='1e8 [ohm]',OpCur=1,Iflt='IF'+k)
        electric_label('BUS_'+k[0],point(f,'A'))
        if k=='AB':electric_label('BUS_B',point(f,'B'))
        else:comp('ground',*point(f,'B'))
        ids['faults'][k]=f.iid
    src=comp('source_1',10,50,Name='External_DC_Equivalent',Type=6,Grnd=0,Spec=0,Cntrl=1,AC=0,Tc='0 [s]',CUR='ISOURCE')
    electric_label('DCSRC',point(src,'NA'));electric_label('N',point(src,'NB'))
    sig(src,'Mag','EDC');ids['sources']['DC']=src.iid
    r=comp('resistor',8,30,R='5 [ohm]',Name='Rdc');ids['rdc']=r.iid
    electric_label('DCSRC',point(r,'A'));electric_label('RDC',point(r,'B'))
    l=comp('inductor',8,20,L='0.5 [H]',Name='Ldc');ids['ldc']=l.iid
    electric_label('RDC',point(l,'A'));electric_label('IDC_NODE',point(l,'B'))
    am=comp('ammeter',8,10,Name='Idc_meas');electric_label('P',point(am,'N1'));electric_label('IDC_NODE',point(am,'N2'))
    v=comp('voltmeter',16,16,Name='Vdc_meas')
    electric_label('P',point(v,'N1'));electric_label('N',point(v,'N2'))
    channels={**{f'IT{k}':'kA' for k in range(1,7)},**{f'VT{k}':'kV' for k in range(1,7)},
              **{f'G{k}':'' for k in range(1,7)},**{f'GammaT{k}':'s' for k in range(1,7)},
              **{f'VAC{k}':'kV' for k in 'ABC'},**{f'VPCC{k}':'kV' for k in 'ABC'},
              **{f'IG{k}':'kA' for k in 'ABC'},'Idc_meas':'kA','Vdc_meas':'kV','AlphaRef':'deg',
              'FaultActive':'','SagApplied':''}
    for j,(name,unit) in enumerate(channels.items()):
        x=10+(j%6)*15;y=125+(j//6)*8
        label(name,(x,y));wire((x,y),(x+3,y))
        comp('pgb',x+3,y,Name=name,UseSignalName=0,Units=unit,Group='LCC')
    c.create_annotation(40,3,'STANDALONE SIX-PULSE LCC INVERTER',
                        'T1/T3/T5 upper; T4/T6/T2 lower. Firing T1 to T6. P-N is negative in inverter operation.')
    c.create_annotation(35,96,'ORIGINAL SOURCE AND FIRING CONTROLLER',
                        '50 Hz reference clock; 120 degree gate windows. Signed external source commands. Minimum extinction time 200 us.')
    p.save()
    (dest/'component_ids.json').write_text(json.dumps(ids,indent=2))
    (ROOT/'config/model_parameters.json').write_text(json.dumps(NOMINAL,indent=2))
    return p


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=0);args=ap.parse_args()
    app=mhi.pscad.connect(port=args.port);assert app.licensed()
    p=build(app);print(p.filename,flush=True)
    p.build();print([(m.status,m.text) for m in p.messages()],flush=True)
