"""Package the complete static student laboratory, report and license notices."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
def package():
    folder=ROOT/'dist';folder.mkdir(exist_ok=True);target=folder/'HVDC_LCC_Lab_Offline.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=8) as archive:
        for file in sorted((ROOT/'docs').rglob('*')):
            if file.is_file() and 'superpowers' not in file.parts:archive.write(file,file.relative_to(ROOT/'docs'))
        archive.write(ROOT/'reports/HVDC_LCC_Technical_Report.pdf','HVDC_LCC_Technical_Report.pdf')
        for name in ['LICENSE','THIRD_PARTY_NOTICES.md']:archive.write(ROOT/name,name)
        archive.writestr('START_HERE.txt','HVDC Commutation Failure Lab\n\nExtract this entire archive to a folder. Open index.html in a recent Chrome or Edge browser. Keep assets and data beside the pages. No PSCAD or Python installation is needed.\n\nThe browser replays actual PSCAD recordings; it does not run an EMT solver. Read technical_report.html or HVDC_LCC_Technical_Report.pdf for assumptions and evidence.\n\nSource and updates: https://github.com/angelohafner/hvdc-lcc-commutation-failure-lab\n')
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert 'index.html' in archive.namelist()
        assert sum(x.startswith('modules/') and x.endswith('.html') for x in archive.namelist())==7
        for file in (ROOT/'docs/data/cases').glob('*.js'):assert archive.read('data/cases/'+file.name)==file.read_bytes()
        result=dict(file=target.name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),files=len(archive.namelist()),crc_and_dataset_bytes_verified=True)
    (folder/'manifest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return target
if __name__=='__main__':package()
