"""Package full-resolution PSCAD recordings for offline classic-script loading."""
from pathlib import Path
import base64,hashlib,json,zlib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def export():
    dest=ROOT/'docs/data/cases';dest.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for folder in sorted((ROOT/'results/processed').iterdir()):
        if not (folder/'summary.json').exists() or folder.name.startswith('NUM-'):continue
        meta=json.loads((folder/'metadata.json').read_text());summary=json.loads((folder/'summary.json').read_text())
        if summary['physical_consistency']!='pass':continue
        events=json.loads((folder/'events.json').read_text());z=np.load(folder/'signals.npz');t=z['time'];mask=t>=.2
        fields=[k for k in z.files if k!='time' and not k.startswith('GammaT')]
        matrix=np.column_stack([z[k][mask] for k in fields]).astype('<f4')
        words=matrix.T.copy().view('<u4');deltas=words.copy();deltas[:,1:]=words[:,1:]^words[:,:-1]
        encoded=deltas.view('u1').reshape(len(fields),len(matrix),4).transpose(0,2,1).copy().tobytes()
        error={k:float(np.max(abs(matrix[:,j].astype(float)-z[k][mask]))) for j,k in enumerate(fields)}
        payload=dict(case_id=folder.name,title=summary['title'],summary=summary,parameters=meta['parameters'],
                     events=events,fields=fields,units=meta['units'],t0=float(t[mask][0]),
                     dt=meta['parameters']['time_step_us']*1e-6,samples=int(mask.sum()),
                     data_layout='xor-byteplanes-v1',
                     encoding='zlib + base64, column-wise XOR float32 byte planes; no time downsampling',
                     quantization_max_abs_error=error,
                     provenance={k:meta[k] for k in ['project','project_sha256','output_sha256','pscad_version','compiler','start_utc','finish_utc','execution_status','source_hashes_verified']},
                     data=base64.b64encode(zlib.compress(encoded,9)).decode())
        path=dest/(folder.name+'.js')
        path.write_text('window.registerCase('+json.dumps(payload,separators=(',',':'),allow_nan=False)+');',encoding='utf-8')
        entry=dict(id=folder.name,title=summary['title'],file='data/cases/'+path.name,bytes=path.stat().st_size,
                   sha256=hashlib.sha256(path.read_bytes()).hexdigest(),parameters=meta['parameters'],summary=summary)
        manifest.append(entry)
        print(folder.name,path.stat().st_size,flush=True)
    data=dict(schema_version=1,source='Actual PSCAD 5.1.0 EMTDC output',publication_status='public_release',
              cases=manifest,notes=['Gate commands and measured conduction are different signals.',
                'The browser replays recordings and does not solve an EMT model.',
                'Full native samples from 0.2 s onward are retained; float32 conversion errors are declared per signal.',
                'Inconclusive attempts are not counted as verified failures.'])
    (ROOT/'docs/data/manifest.json').write_text(json.dumps(data,indent=2))
    (ROOT/'docs/data/manifest.js').write_text('window.LAB_MANIFEST='+json.dumps(data,separators=(',',':'))+';')
    return data

if __name__=='__main__':export()
