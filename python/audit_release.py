"""Audit the current shareable checkout and static links before local packaging."""
from pathlib import Path
import hashlib,json,re,subprocess,getpass
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ['src','href'] and v:self.links.append(v)
def audit():
    files=[ROOT/p for p in subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()]
    issues=[];total=0
    secret=re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
    for p in files:
        if not p.is_file():continue
        total+=p.stat().st_size;rel=p.relative_to(ROOT).as_posix()
        if p.suffix.lower() in ['.exe','.dll','.obj','.o','.bakx','.psmx','.out','.inf'] or '/node_modules/' in '/'+rel:issues.append('Excluded build/raw dependency: '+rel)
        if p.stat().st_size>50*1024*1024:issues.append('File exceeds 50 MiB: '+rel)
        if p.suffix in ['.py','.js','.cjs','.html','.css','.md','.json','.pscx','.txt']:
            s=p.read_text(encoding='utf-8')
            if secret.search(s):issues.append('Credential-like text: '+rel)
            if getpass.getuser() in s:issues.append('Local OS-account stamp: '+rel)
    for p in (ROOT/'docs').rglob('*.html'):
        h=Links();h.feed(p.read_text(encoding='utf-8'))
        for link in h.links:
            u=urlsplit(link)
            if u.scheme or u.netloc or not u.path:continue
            target=p.parent/unquote(u.path)
            if not target.exists():issues.append('Missing link '+str(p.relative_to(ROOT))+': '+link)
    result=dict(scope='Current shareable checkout only; Git history and a future public deployment require their own publication check',
                file_count=len(files),total_bytes=total,issues=issues,passed=not issues)
    (ROOT/'reports/release_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if issues:raise SystemExit(1)
if __name__=='__main__':audit()
