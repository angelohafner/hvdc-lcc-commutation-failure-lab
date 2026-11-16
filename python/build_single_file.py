"""Bundle the existing laboratory and all recorded student data into one offline HTML."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
RUNTIME=ROOT/'python/single_file_runtime.js'

def data_uri(path):
    mime={'.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf',
          '.png':'image/png','.svg':'image/svg+xml','.jpg':'image/jpeg'}[path.suffix]
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()

def build(output=None):
    output=Path(output or ROOT/'dist/HVDC_LCC_Virtual_Laboratory.html')
    resources={};inputs={}
    def read(path):
        path=path.resolve()
        path.relative_to(ROOT)
        raw=path.read_bytes();inputs[path.relative_to(ROOT).as_posix()]=hashlib.sha256(raw).hexdigest()
        return raw.decode('utf-8')
    def resource(path):
        key=path.resolve().relative_to(DOCS).as_posix()
        if key not in resources:
            text=read(path)
            if path.suffix=='.css':
                def font(match):
                    name=match[1].strip('"\'');asset=(path.parent/name).resolve()
                    asset.relative_to(DOCS)
                    inputs[asset.relative_to(ROOT).as_posix()]=hashlib.sha256(asset.read_bytes()).hexdigest()
                    return 'url('+data_uri(asset)+')'
                text=re.sub(r'url\(([^)]+)\)',font,text)
            if key=='assets/js/lab.js':
                # Keep the tested plot/circuit/assessment engine. Replace only file loading.
                start=text.index('window.registerCase=async payload=>{')
                end=text.index('function indexAt(',start)
                text=text[:start]+"async function loadCase(id){return parent.HVDC_SINGLE_FILE.loadCase(id);}\n"+text[end:]
                text=text.replace('const cache=new Map(),pending=new Map();\n','')
            resources[key]=text
        return key
    manifest=json.loads(read(DOCS/'data/manifest.json'))
    recordings={}
    for entry in manifest['cases']:
        path=DOCS/entry['file'];raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['sha256']:
            raise ValueError('Dataset hash mismatch: '+entry['id'])
        source=read(path)
        if not source.startswith('window.registerCase(') or not source.endswith(');'):
            raise ValueError('Unexpected recording wrapper: '+entry['id'])
        recordings[entry['id']]=json.loads(source[len('window.registerCase('):-2])
    pages={}
    paths=[DOCS/'index.html',*sorted((DOCS/'modules').glob('*.html')),DOCS/'technical_report.html']
    if len(paths)!=9:raise ValueError('Expected eight modules and the technical report')
    for i,path in enumerate(paths):
        text=read(path);scripts=[]
        def script(match):
            scripts.append(resource(path.parent/match[1]));return ''
        text=re.sub(r'<script\b[^>]*\bsrc="([^"]+)"[^>]*></script>',script,text)
        text=re.sub(r'<link\b[^>]*rel="stylesheet"[^>]*href="([^"]+)"[^>]*>',
                    lambda m:'<style data-offline-resource="'+resource(path.parent/m[1])+'"></style>',text)
        def image(match):
            asset=(path.parent/match[1]).resolve();asset.relative_to(DOCS)
            inputs[asset.relative_to(ROOT).as_posix()]=hashlib.sha256(asset.read_bytes()).hexdigest()
            return match[0].replace(match[1],data_uri(asset))
        text=re.sub(r'<img\b[^>]*src="([^"]+)"[^>]*>',image,text)
        text=text.replace('</body>',''.join('<script data-offline-resource="'+s+'"></script>' for s in scripts)+'</body>')
        # Online source/download links remain optional; the artifact itself needs no network.
        text=text.replace('English · Offline ready','English · All resources embedded')
        pages['report' if i==8 else str(i)]=dict(file=path.name,title=re.search(r'<title>(.*?)</title>',text)[1],html=text)
    notices={'Project license':read(ROOT/'LICENSE'),'Third-party notices':read(ROOT/'THIRD_PARTY_NOTICES.md'),
             'KaTeX':read(DOCS/'assets/vendor/katex/LICENSE')}
    bundle=dict(schema_version=1,manifest=manifest,recordings=recordings,resources=resources,pages=pages,notices=notices,
                source_sha256=inputs,scope='Original PSCAD recordings, unchanged float32 browser representation; no solver or synthetic transients.')
    packed=json.dumps(bundle,separators=(',',':'),ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    runtime=RUNTIME.read_text(encoding='utf-8').replace('</script','<\\/script')
    html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; frame-src 'self' about:; connect-src 'none'; object-src 'none'; base-uri 'none'">
<title>HVDC-LCC Virtual Laboratory | Self-contained edition</title><style>
:root{font:16px/1.4 Segoe UI,Arial,sans-serif;color:#183c50;background:#eef4f6;color-scheme:light}*{box-sizing:border-box}body{margin:0;height:100vh;height:100dvh;display:grid;grid-template-rows:auto minmax(0,1fr)}.shell{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:8px 14px;background:#f3f8fa;border-bottom:1px solid #cfdee4}.shell strong{font-size:.85rem}.shell select{flex:1;min-width:180px;max-width:520px}.shell button,.shell select{font:inherit;font-size:.86rem;min-height:38px;border:1px solid #aebfc9;border-radius:6px;background:white;padding:6px 10px;color:inherit}.shell button{cursor:pointer}.shell button:disabled{opacity:.5}.offline{font-size:.75rem;color:#08775d}.stage{position:relative;min-height:0}.stage iframe{display:block;border:0;width:100%;height:100%;background:#eef4f6}.stage iframe[hidden]{display:none}.loading{position:absolute;inset:10px auto auto 15px;padding:12px;background:white;z-index:10}.loading[hidden]{display:none}dialog{width:min(900px,94vw);max-height:90vh;max-height:90dvh;border:1px solid #aebfc9;border-radius:10px;padding:22px;color:inherit}dialog::backdrop{background:#183c5066}pre{white-space:pre-wrap;word-break:break-word;font:12px/1.5 Consolas,monospace}button:focus-visible,select:focus-visible{outline:3px solid #d99b32;outline-offset:2px}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}@media(max-width:600px){.shell{gap:5px;padding:6px 8px}.shell strong{width:100%}.shell select{max-width:none;min-width:0;width:100%;flex-basis:100%}.offline{margin-left:auto}.shell button{font-size:.76rem;padding:5px 8px}}
</style></head><body><header class="shell"><strong>HVDC-LCC virtual laboratory</strong><label class="sr-only" for="module-switch">Learning module</label><select id="module-switch" aria-label="Learning module"></select><button id="module-previous" aria-label="Previous module">Previous</button><button id="module-next" aria-label="Next module">Next</button><button id="notices-open">Licenses &amp; provenance</button><span class="offline">Self-contained · Offline</span></header><main class="stage" id="stage"><p class="loading" id="bundle-status" role="status">Opening embedded laboratory…</p></main><dialog id="notices"><button id="notices-close">Close</button><h1>Licenses and data provenance</h1><p>All required resources are inside this file. Optional external reference links require an Internet connection. A recent Chrome or Edge browser is required. This file replays native PSCAD recordings; it does not run an EMT solver.</p><div id="notices-content"></div></dialog><noscript>Enable JavaScript to use this interactive offline laboratory.</noscript>
'''+ '<script id="single-file-bundle" type="application/json">'+packed+'</script><script>'+runtime+'</script></body></html>'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(html,encoding='utf-8',newline='\n')
    result=dict(file=output.name,bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                modules=8,technical_report=True,recordings=len(recordings),recorded_sample_times=sum(p['samples'] for p in recordings.values()),
                recorded_signal_values=sum(p['samples']*len(p['fields']) for p in recordings.values()),all_source_dataset_hashes_verified=True)
    output.with_suffix('.manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2));return output

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args();build(args.output)
