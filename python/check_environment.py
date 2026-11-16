"""Report relevant software availability without dumping user settings or credentials."""
from pathlib import Path
import argparse,importlib.metadata,importlib.util,json,platform,shutil,sys

def check(port=0):
    result=dict(python=sys.version.split()[0],platform=platform.system(),
                git_available=bool(shutil.which('git')),gh_available=bool(shutil.which('gh')),
                packages={})
    for package in ['mhi.pscad','numpy','matplotlib','schemdraw','PyYAML']:
        try:result['packages'][package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:result['packages'][package]=None
    try:
        import mhi.pscad
        result['pscad_installations']=mhi.pscad.versions()
        app=mhi.pscad.connect(port=port)
        result.update(pscad_version=app.version,licensed=app.licensed(),
                      configured_compiler=app.settings()['fortran_version'],available_compilers=app.setting_range('fortran_version'))
    except Exception as exc:result['pscad_connection_error']=str(exc)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=0);p.add_argument('--output');a=p.parse_args()
    data=json.dumps(check(a.port),indent=2);print(data)
    if a.output:Path(a.output).write_text(data)
