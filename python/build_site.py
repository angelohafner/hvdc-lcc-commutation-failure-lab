"""Generate the eight static English laboratory entry pages."""
from pathlib import Path
import html,json
ROOT=Path(__file__).resolve().parents[1]
PAGES=[('index.html','HVDC Commutation Failure Lab'),('01_lcc_inverter_fundamentals.html','Understanding the Six-Pulse Inverter'),('02_commutation_and_extinction_angle.html','Commutation and Extinction Angle'),('03_normal_vs_failed_commutation.html','Normal Versus Failed Commutation'),('04_ac_faults_and_commutation_failures.html','AC Faults and Commutation Failure'),('05_repeated_commutation_failures.html','Repeated Failures and Recovery'),('06_parameters_and_mitigation.html','Parameters and Mitigation'),('07_interactive_exercises.html','Interactive Exercises')]

def build():
    svg=(ROOT/'docs/assets/svg/inverter.svg').read_text()
    bolt='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 2 4 13h7l-1 9 10-13h-7z"/></svg>'
    for i,(file,title) in enumerate(PAGES):
        base='' if i==0 else '../'
        path=ROOT/'docs'/('' if i==0 else 'modules')/file;path.parent.mkdir(exist_ok=True)
        previous=(f'<a href="{base}index.html">← Learning hub</a>' if i<=1 else f'<a href="{PAGES[i-1][0]}">← Previous module</a>')
        following=(f'<a href="{("modules/" if i==0 else "")+PAGES[i+1][0]}">Next module →</a>' if i<7 else f'<a href="{base}technical_report.html">Technical report →</a>')
        page=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Interactive engineering laboratory with real PSCAD thyristor currents, commutation waveforms, and guided exercises."><title>{html.escape(title)} | HVDC Lab</title><link rel="stylesheet" href="{base}assets/css/lab.css"><link rel="stylesheet" href="{base}assets/vendor/katex/katex.min.css"><script defer src="{base}assets/vendor/katex/katex.min.js"></script><script defer src="{base}assets/js/content.js"></script><script defer src="{base}data/manifest.js"></script><script defer src="{base}assets/js/lab.js"></script></head>
<body data-module="{i}" class="level-beginner"><a class="skip" href="#main">Skip to laboratory</a><header class="topbar"><a class="brand" href="{base}index.html">{bolt} HVDC Commutation Failure Lab</a><div class="top-actions"><span class="badge">English · Offline ready</span><label for="level" class="sr-only">Learning level</label><select id="level"><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select><button id="mode" aria-pressed="false">Presentation mode</button><button id="details-toggle" aria-pressed="true">Show / hide explanations</button></div></header>
{'<div class="layout"><aside class="sidebar"><nav id="module-nav" aria-label="Learning modules"></nav></aside>' if i else ''}<main id="main" {'class="hub"' if i==0 else ''}><div class="intro study-copy"><div><p class="eyebrow">{'Interactive engineering laboratory' if i==0 else f'Module {i:02d} / 07'}</p><h1 id="page-title">{html.escape(title)}</h1><p id="page-objective" class="lead"></p></div></div><div id="lab-content"></div><nav class="footer-nav" aria-label="Previous and next module">{previous}{following}</nav><p class="publication"><a href="https://github.com/angelohafner/hvdc-lcc-commutation-failure-lab">GitHub source and validation</a> · <a href="https://github.com/angelohafner/hvdc-lcc-commutation-failure-lab/releases/latest">Download the offline laboratory</a></p></main>{'</div>' if i else ''}<footer class="footer">Original six-pulse inverter study · Recorded PSCAD/EMTDC data · <a href="{base}technical_report.html">Assumptions, validation, and offline instructions</a></footer><template id="circuit-template">{svg}</template><dialog id="diagram-dialog"><div class="card-head"><h2>Measured inverter conduction</h2><button id="close-diagram">Close</button></div><div id="large-circuit" class="schematic"></div><p class="muted">Playback is paused. Matching phase labels connect the bridge and AC equivalent.</p></dialog><noscript><p class="error">Enable JavaScript to replay the recorded data. The technical report remains readable without it.</p></noscript></body></html>'''
        path.write_text(page,encoding='utf-8')
    (ROOT/'docs/.nojekyll').write_text('')
    print('Built eight laboratory HTML pages')

if __name__=='__main__':build()
