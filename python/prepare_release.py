"""Redact OS account stamps from shareable projects; preserve native archives."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
STAMP=re.compile(r'(<param name="(?:creator|revisor)" value=")[^,"]*(,[^"]*")')
def normalized(text):return STAMP.sub(r'\1AUTHOR\2',text)
def prepare():
    manifest=[]
    for path in sorted((ROOT/'pscad').rglob('*.pscx')):
        original=path.read_text();redacted=STAMP.sub(r'\1Angelo Hafner\2',original)
        if redacted!=original:path.write_text(redacted,encoding='utf-8')
        row=dict(project=path.relative_to(ROOT).as_posix(),shareable_project_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),redaction='Creator/revisor OS-account stamps only; native execution archives unchanged')
        receipt=next((p for p in (ROOT/'results/raw').glob('*/receipt.json') if not p.parent.name.startswith('REJECTED') and json.loads(p.read_text())['project']==row['project']),None)
        if receipt:
            data=json.loads(receipt.read_text());archived=receipt.parent/path.name
            if normalized(archived.read_text())!=normalized(path.read_text()):raise ValueError('Unexpected executable-model difference: '+path.name)
            row.update(case_id=data['case_id'],executed_project_sha256=data['project_sha256'],only_author_metadata_changed=True)
        manifest.append(row)
    (ROOT/'results/summary/release_project_hashes.json').write_text(json.dumps(manifest,indent=2))
    (ROOT/'docs/data/release_project_hashes.json').write_text(json.dumps(manifest,indent=2))
    print('Prepared',len(manifest),'original PSCAD projects; executable content preserved')
if __name__=='__main__':prepare()
