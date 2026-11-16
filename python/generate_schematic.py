"""Native Schemdraw SCR symbols, with semantic SVG groups for measured-state replay."""
from pathlib import Path
import xml.etree.ElementTree as ET
import schemdraw
import schemdraw.elements as elm

ROOT=Path(__file__).resolve().parents[1]

def generate():
    d=schemdraw.Drawing(canvas='svg',show=False)
    d.config(font='Arial',fontsize=12,lw=1.6,color='#506574')
    colors={f'#ab000{k}':f'valve-T{k}' for k in range(1,7)}
    colors['#ab0010']='dc-path'
    for phase,x,up,low in [('A',5,1,4),('B',8,3,6),('C',11,5,2)]:
        d.add(elm.SCR().at((x,3)).up().length(3).color(f'#ab000{up}').label(f'T{up}',loc='top'))
        d.add(elm.SCR().at((x,0)).up().length(3).color(f'#ab000{low}').label(f'T{low}',loc='top'))
        d.add(elm.Dot().at((x,3)).label(phase,loc='right',ofst=.25))
    d.add(elm.Line().at((5,6)).to((11,6)).color('#ab0010').label('P: DC bridge terminal',loc='top'))
    d.add(elm.Line().at((5,0)).to((11,0)).color('#ab0010').label('N: DC bridge terminal',loc='bottom'))
    d.add(elm.Inductor().at((5,6)).to((2.5,6)).color('#ab0010').label('Ldc'))
    d.add(elm.ResistorIEEE().at((2.5,6)).to((0,6)).color('#ab0010').label('Rdc'))
    dc=d.add(elm.SourceV().at((0,6)).down().length(6).color('#ab0010').label('DC equivalent',loc='top'))
    assert abs(dc.end.x)<1e-9 and abs(dc.end.y)<1e-9
    d.add(elm.Line().at((0,0)).to((5,0)).color('#ab0010'))
    for phase,y in [('A',5.6),('B',3),('C',.4)]:
        color={'A':'#ab0021','B':'#ab0022','C':'#ab0023'}[phase];colors[color]='phase-'+phase
        d.add(elm.Dot(open=True).at((14,y)).color(color).label(phase,loc='left',ofst=.25))
        d.add(elm.Inductor().at((14,y)).to((16,y)).color(color).label('Lc',loc='top'))
        d.add(elm.Dot().at((16,y)).label('PCC',loc='bottom',ofst=.18))
        d.add(elm.ResistorIEEE().at((16,y)).to((18,y)).color(color).label('Rg',loc='top'))
        d.add(elm.Inductor().at((18,y)).to((20,y)).color(color).label('Lg',loc='top'))
        ac=d.add(elm.SourceSin().at((20,y)).right().length(2).color(color).label('e'+phase,loc='top'))
        assert abs(ac.end.x-22)<1e-9 and abs(ac.end.y-y)<1e-9
        d.add(elm.Ground().at((22,y)))
    raw=d.get_imagedata('svg');root=ET.fromstring(raw)
    ns='{http://www.w3.org/2000/svg}';ET.register_namespace('',ns[1:-1])
    root.attrib.pop('width',None);root.attrib.pop('height',None)
    root.set('role','img');root.set('aria-label','Six-pulse inverter and labeled three-phase Thevenin equivalent')
    groups={color:ET.Element(ns+'g',{'id':name,'class':'electrical '+('valve' if name.startswith('valve') else 'path'),
                                  'style':'color:#506574'}) for color,name in colors.items()}
    # SVG backend emits device paths and text as direct child nodes.
    for node in list(root):
        serialized=ET.tostring(node,encoding='unicode')
        matching=[color for color in colors if color in serialized]
        if len(matching)==1:
            color=matching[0];root.remove(node)
            for element in node.iter():
                for key,value in list(element.attrib.items()):element.set(key,value.replace(color,'currentColor'))
            groups[color].append(node)
    for group in groups.values():root.append(group)
    for color,group in groups.items():
        if not len(group):raise RuntimeError('Missing schematic group '+colors[color])
    for location in ['figures/schematics/inverter.svg','docs/assets/svg/inverter.svg']:
        path=ROOT/location;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(ET.tostring(root,encoding='unicode'))
    print('Created native-symbol SVG with six valve groups')

if __name__=='__main__':generate()
