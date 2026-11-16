"""Rebuild published artifacts from accepted local native evidence, without rerunning PSCAD."""
import json
from process_results import ROOT,process_case
from validate_study import audit
from generate_plots import plots
from build_comparisons import build as comparisons
from export_html_data import export
from generate_schematic import generate
from build_site import build
from build_report import build as report
from prepare_release import prepare

if __name__=='__main__':
    cases=[]
    for folder in sorted((ROOT/'results/raw').iterdir()):
        if folder.name.startswith('REJECTED') or not (folder/'receipt.json').exists():continue
        receipt=json.loads((folder/'receipt.json').read_text())
        if receipt['execution_status']!='success':continue
        process_case(folder);cases.append(folder.name)
    result=audit()
    if not result['pass_all']:raise SystemExit('Audit failed; no release export')
    for case in cases:plots(case)
    comparisons();prepare();export();generate();build();report()
