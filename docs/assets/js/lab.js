'use strict';
const $=(q,r=document)=>r.querySelector(q), $$=(q,r=document)=>[...r.querySelectorAll(q)];
const lesson=LAB_LESSONS[Number(document.body.dataset.module||0)];
const base=lesson.id===0?'':'../';
const colors=['#1265b0','#be472c','#07816e','#9061ad','#a57113','#516c7c'];
const phase={1:'A',3:'B',5:'C',4:'A',6:'B',2:'C'};
const cache=new Map(),pending=new Map();
const S={data:null,reference:null,event:null,refEvent:null,time:0,start:0,end:1,playing:false,speed:1,valve:1,guide:0,view:'commutation',detail:true,compare:false,loadVersion:0,level:'beginner'};
function fmt(n,d=2){return Number.isFinite(n)?n.toFixed(d):'Not established';}
function escapeText(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function math(){if(window.katex)$$('.math').forEach(el=>{if(!el.dataset.rendered){katex.render(el.textContent,el,{throwOnError:false,displayMode:el.classList.contains('block')});el.dataset.rendered='1';}});}
function badge(e){return e?.verified_failure?'fail':e?.classification==='normal'?'good':'warn';}
function readable(s){return String(s||'').replaceAll('_',' ');}
window.registerCase=async payload=>{
  const request=pending.get(payload.case_id);
  try{
    const encoded=Uint8Array.from(atob(payload.data),c=>c.charCodeAt(0));
    const stream=new Blob([encoded]).stream().pipeThrough(new DecompressionStream('deflate'));
    const bytes=await new Response(stream).arrayBuffer();
    if(bytes.byteLength!==payload.samples*payload.fields.length*4)throw Error('Dataset size does not match its declared shape.');
    const matrix=new DataView(bytes);const signals={};
    payload.fields.forEach((key,j)=>{const a=new Float32Array(payload.samples),scratch=new DataView(new ArrayBuffer(4));let previous=0;for(let i=0;i<a.length;i++){
      if(payload.data_layout==='xor-byteplanes-v1'){const start=j*4*a.length;let word=0;for(let b=0;b<4;b++)word|=matrix.getUint8(start+b*a.length+i)<<(8*b);previous=(previous^word)>>>0;scratch.setUint32(0,previous,true);a[i]=scratch.getFloat32(0,true);}
      else a[i]=matrix.getFloat32((i*payload.fields.length+j)*4,true);
    }signals[key]=a;});
    delete payload.data;payload.signals=signals;cache.set(payload.case_id,payload);request?.resolve(payload);
  }catch(error){request?.reject(error);}finally{pending.delete(payload.case_id);}
};
async function loadCase(id){
  if(cache.has(id))return cache.get(id);
  if(pending.has(id))return pending.get(id).promise;
  const entry=LAB_MANIFEST.cases.find(x=>x.id===id);if(!entry)throw Error('This recording is not available: '+id);
  let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});pending.set(id,{promise,resolve,reject});
  const script=document.createElement('script');script.src=base+entry.file;script.onerror=()=>{pending.delete(id);reject(Error('Could not load '+id+'. Keep the data folder beside these HTML files.'));};document.head.append(script);return promise;
}
function indexAt(d,t){return Math.max(0,Math.min(d.samples-1,Math.round((t-d.t0)/d.dt)));}
function value(d,key,t){return d.signals[key]?.[indexAt(d,t)]??NaN;}
function instantiateCircuit(container){
  container.innerHTML=$('#circuit-template').innerHTML;
  $$('[id]',container).forEach(el=>{const id=el.id;el.dataset.part=id;if(id.startsWith('valve-T')){el.dataset.valve=id.slice(6);el.addEventListener('click',()=>selectValve(Number(id.slice(7))));}el.id=container.id+'-'+id;});
}
function navigation(){
  const nav=$('#module-nav');if(!nav)return;
  nav.innerHTML=LAB_LESSONS.map(l=>`<a href="${l.id===0?base+'index.html':(lesson.id===0?'modules/':'')+l.file}" ${l.id===lesson.id?'aria-current="page"':''}>${String(l.id).padStart(2,'0')} · ${l.short}</a>`).join('')+`<a href="${base}technical_report.html">Technical report</a>`;
}
function viewerMarkup(){
  return `<section class="card" aria-label="Recorded PSCAD laboratory">
    <div class="card-head"><h2>${lesson.id===0?'Explore a recorded commutation':'Recorded experiment'}</h2><span class="badge good">Actual PSCAD data</span></div>
    <div class="controls"><div class="control grow"><label for="case-select">PSCAD recording</label><select id="case-select"></select></div>
    <div class="control grow"><label for="event-select">Firing attempt</label><select id="event-select"></select></div>
    <div class="control"><label for="signal-view">Waveform view</label><select id="signal-view"><option value="commutation">Commutation detail</option><option value="system">AC and DC system</option><option value="valves">Six valve currents</option><option value="gates">Six gate commands</option><option value="angles">Angles and margin</option></select></div></div>
    <div id="case-note" class="fault-description study-copy"></div>
    <div class="playbar"><button id="play" class="primary" aria-pressed="false">Play</button><button id="pause">Pause</button><button id="reset">Reset</button><div class="control"><label for="speed">Playback: electrical cycles/s</label><select id="speed"><option value="0.25">0.25</option><option value="0.5">0.5</option><option value="1" selected>1</option><option value="2">2</option></select></div></div>
    <div class="timecontrol"><div class="time-label"><label for="time">Time cursor</label><output id="time-value"></output></div><input id="time" type="range" min="0" max="10000" value="0" aria-label="Time cursor"></div>
    ${lesson.id===1?'<div class="timecontrol"><div class="time-label"><label for="electrical-angle">Electrical angle in the selected steady-state cycle</label><output id="angle-value">0°</output></div><input id="electrical-angle" type="range" min="0" max="360" step="0.5" value="0"></div>':''}
    <div class="readouts"><div class="readout"><span>DC current</span><strong id="reading-current">—</strong></div><div class="readout"><span>Bridge DC voltage</span><strong id="reading-voltage">—</strong></div><div class="readout"><span>DC power into bridge</span><strong id="reading-power">—</strong></div><div class="readout"><span>Selected attempt</span><strong id="reading-class" style="font-size:.9rem">—</strong></div></div>
    <div class="diagram-guide"><div><div class="card-head"><h3>Measured conduction</h3><button id="enlarge" class="small">Enlarge circuit</button></div><div id="circuit" class="schematic"></div><p class="diagram-caption">Matching A/B/C labels connect the bridge to the AC equivalent. The DC supply floats across P–N. Highlighted paths follow measured current; gate status is shown separately.</p><div id="valve-list" class="valve-list"></div><div id="valve-info" class="valve-info" aria-live="polite"></div></div>
    <div class="study-copy"><div class="guide"><p id="guide-count" class="guide-step"></p><h3 id="guide-title"></h3><p id="guide-text"></p><div class="guide-controls"><button id="previous-step">Previous step</button><button id="next-step">Next step</button></div></div></div></div>
    <div class="toolbar"><button id="focus-event">Focus event</button><button id="whole-record">Disturbance overview</button><button id="zoom-in" aria-label="Zoom in">Zoom +</button><button id="zoom-out" aria-label="Zoom out">Zoom −</button><button id="pan-left" aria-label="Pan earlier">← Pan</button><button id="pan-right" aria-label="Pan later">Pan →</button><button id="reset-view">Reset view</button><button id="export-plot">Export figure</button></div>
    <div class="controls"><label><input id="compare" type="checkbox"> Compare recordings</label><div class="control grow" id="reference-control" hidden><label for="reference-select">Reference recording</label><select id="reference-select"></select></div></div>
    <p id="alignment-note" class="plot-note">All plots and circuit highlights share the same recorded time cursor.</p>
    <div id="plot-columns" class="plot-columns"><div><h3 id="primary-name" class="plot-title"></h3><div id="primary-plots" class="plots"></div></div><div id="reference-column" hidden><h3 id="reference-name" class="plot-title"></h3><div id="reference-plots" class="plots"></div></div></div>
    <div id="value-inspector" class="inspector"></div><p class="plot-note">Drag or click a waveform to move the cursor. Zoom retains native time samples; overview rendering keeps local minima and maxima.</p>
    <div class="evidence study-copy"><h3>Evidence for this attempt</h3><div id="event-evidence"></div></div>
    <details class="advanced"><summary>Parameters, source files, and validation</summary><div id="parameters" class="table-wrap"></div><pre id="provenance"></pre></details>
    <div id="load-status" class="busy" role="status">Loading a verified recording…</div>
  </section>`;
}
function buildPage(){
  navigation();$('#page-title').textContent=lesson.title;$('#page-objective').textContent=lesson.objective;
  const target=$('#lab-content');
  if(lesson.id===0){
    target.innerHTML=`<section class="card"><div class="card-head"><div><h2>HVDC Commutation Failure Lab</h2><small>Interactive PSCAD-based learning modules</small></div><span class="badge">Educational</span></div><div class="cards">${LAB_LESSONS.slice(1).map(l=>`<a class="module-link" href="modules/${l.file}"><span class="number">${String(l.id).padStart(2,'0')}</span><div><h3>${l.short}</h3><p>${l.tagline}</p></div></a>`).join('')}<a class="module-link" href="technical_report.html"><span class="number">↗</span><div><h3>Technical report</h3><p>Study the model, evidence, and limitations.</p></div></a></div></section><div class="metrics-line"><div><strong>${LAB_MANIFEST.cases.filter(c=>/^CF-\d{2}$/.test(c.id)).length}</strong><span>core case recordings</span></div><div><strong>6</strong><span>individually measured valves</span></div><div><strong>10 μs</strong><span>main native sample interval</span></div></div><div class="note study-copy"><strong>Recommended path:</strong> fundamentals → angles → normal versus failure → faults → repeated events → mitigation → exercises. The browser replays measured recordings; it does not run an EMT solver.</div>${viewerMarkup()}<section class="card"><h2>Available recordings</h2><div id="case-overview" class="table-wrap"></div></section>`;
  }else{
    target.innerHTML=`<section class="card study-copy"><h2>Before you begin</h2><p><strong>Prior knowledge:</strong> ${lesson.prior}</p><p>${lesson.theory}</p>${lesson.id===2?'<div class="math-display"><span class="math">\\gamma=\\beta-\\mu=180^\\circ-\\alpha-\\mu</span></div><p class="muted">This relation uses the ideal balanced-sinusoidal reference and a successful transfer. Under disturbance, inspect each outgoing valve’s measured reverse-bias interval.</p>':''}</section>${viewerMarkup()}${lesson.id===5?'<section class="card"><div class="card-head"><h2>Firing-attempt timeline</h2><label><input id="only-failures" type="checkbox"> Verified failures only</label></div><p id="timeline-summary"></p><div id="timeline" class="timeline"></div></section>':''}${lesson.id===6?'<section class="card"><h2>Compare the measured outcomes</h2><p>These are distinct PSCAD operating points. The parameter values below describe the chosen recording; changing a selector loads another simulation.</p><div id="mitigation-table" class="table-wrap"></div><div class="math-display"><span class="math">\\mathrm{SCR}=\\frac{V_{LL}^{2}}{|Z_g|P_{base}}</span></div><p class="muted">Here the declared comparison base is 150 MW. Changing grid impedance also changes the operating current in the fixed-source model; this confound is reported.</p></section>':''}${lesson.id===7?'<section id="assessment" class="card"></section>':''}<section class="card study-copy"><h2>What to take away</h2><p>${lesson.takeaway}</p><h3>Try it yourself</h3><p>${lesson.practice}</p><p class="muted">Next: ${lesson.follow}</p></section>`;
  }
  instantiateCircuit($('#circuit'));
  $('#valve-list').innerHTML=Array.from({length:6},(_,j)=>`<button class="valve-button" data-valve-number="${j+1}" aria-pressed="${j===0}">T${j+1}<small>Loading</small></button>`).join('');
  const available=LAB_MANIFEST.cases;
  const preferred={0:['CF-00'],1:['CF-00'],2:['CF-00','CF-01'],3:['CF-00','CF-01','CF-02'],4:available.filter(c=>['CF-02','CF-03','CF-04','CF-05','CF-06'].includes(c.id)||c.id.startsWith('SW-')||c.id.startsWith('INCEPTION')).map(c=>c.id),5:available.filter(c=>['CF-02','CF-07','CF-12','CF-13','CF-14'].includes(c.id)||c.id.startsWith('CF-13-')||c.id.startsWith('REC')).map(c=>c.id),6:available.map(c=>c.id),7:['CF-00','CF-01','CF-02']}[lesson.id];
  const options=ids=>ids.map(id=>{const c=available.find(c=>c.id===id);return c?`<option value="${id}">${id} · ${escapeText(c.title)}</option>`:'';}).join('');
  $('#case-select').innerHTML=options(preferred);$('#reference-select').innerHTML=options(available.map(c=>c.id));
  $('#case-select').value={0:'CF-00',1:'CF-00',2:'CF-00',3:'CF-02',4:'CF-02',5:'CF-12',6:available.some(c=>c.id==='MIT-DC')?'MIT-DC':'CF-02',7:'CF-00'}[lesson.id];
  $('#reference-select').value=lesson.id===6?'CF-02':'CF-00';
  S.compare=[3,6].includes(lesson.id);$('#compare').checked=S.compare;
  S.view=[4,6].includes(lesson.id)?'system':lesson.id===1?'valves':'commutation';$('#signal-view').value=S.view;
  S.detail=![4,6].includes(lesson.id);
  bindControls();math();if(lesson.id===7)buildAssessment();
  if($('#case-overview'))$('#case-overview').innerHTML=summaryTable(available);
  if($('#mitigation-table'))$('#mitigation-table').innerHTML=summaryTable(available.filter(c=>c.id==='CF-02'||c.id.startsWith('MIT-')));
  changeCase();
}
function summaryTable(cases){return `<table><thead><tr><th>Recording</th><th>Verified failures</th><th>Inconclusive attempts</th><th>Peak DC current</th><th>Valid minimum γ</th><th>Stable sequence after event</th></tr></thead><tbody>${cases.map(c=>`<tr><td>${escapeText(c.id)}<br><small>${escapeText(c.title)}</small></td><td>${c.summary.verified_failure_events}</td><td>${c.summary.inconclusive_events}</td><td>${fmt(c.summary.peak_dc_current_A/1000)} kA</td><td>${c.summary.min_valid_gamma_deg===null?'Not established':fmt(c.summary.min_valid_gamma_deg)+'°'}</td><td>${c.summary.verified_failure_events===0&&c.summary.inconclusive_events===0?'No failure observed':c.summary.stable_recovery_delay_s!=null?fmt(c.summary.stable_recovery_delay_s*1000,1)+' ms':'Not established'}</td></tr>`).join('')}</tbody></table>`;}
async function changeCase(){
  pause();const ticket=++S.loadVersion;$('#load-status').hidden=false;$('#load-status').textContent='Loading a verified recording…';
  try{
    const d=await loadCase($('#case-select').value);if(ticket!==S.loadVersion)return;S.data=d;
    $('#event-select').innerHTML=d.events.map(e=>`<option value="${e.event_id}">${e.event_id} · ${fmt(e.time_s,5)} s · ${e.outgoing} → ${e.incoming} · ${readable(e.classification)}</option>`).join('');
    S.event=d.events.find(e=>e.verified_failure)||[...d.events].reverse().find(e=>e.time_s<.55)||d.events[0];
    $('#event-select').value=S.event.event_id;S.guide=0;
    await changeReference(false);if(ticket!==S.loadVersion)return;
    setWindow();updateCaseText();buildPlots();render();renderTimeline();$('#load-status').hidden=true;
  }catch(error){$('#load-status').className='error';$('#load-status').textContent=error.message;}
}
async function changeReference(redraw=true){
  const ticket=S.referenceVersion=(S.referenceVersion||0)+1;
  S.compare=$('#compare').checked;$('#reference-control').hidden=!S.compare;$('#reference-column').hidden=!S.compare;$('#plot-columns').classList.toggle('compare',S.compare);
  if(S.compare){const reference=await loadCase($('#reference-select').value);if(ticket!==S.referenceVersion)return;S.reference=reference;}
  selectReferenceEvent();if(redraw){buildPlots();render();}
}
function selectReferenceEvent(){if(S.reference&&S.event)S.refEvent=S.reference.events.find(e=>e.incoming===S.event.incoming&&e.time_s>=.5&&['normal','reduced_margin'].includes(e.classification))||S.reference.events.find(e=>e.incoming===S.event.incoming)||S.reference.events[0];}
function setWindow(){
  if(S.detail){S.start=Math.max(S.data.t0,S.event.time_s-.001);S.end=Math.min(S.data.t0+(S.data.samples-1)*S.data.dt,S.event.time_s+.0068);S.time=S.event.time_s;}
  else{S.start=S.data.t0;S.end=S.data.t0+(S.data.samples-1)*S.data.dt;S.time=S.event.time_s;}
}
function selectEvent(id){pause();S.event=S.data.events.find(e=>e.event_id===id);$('#event-select').value=id;S.guide=0;S.detail=true;selectReferenceEvent();setWindow();buildPlots();render();renderTimeline();}
function updateCaseText(){
  const d=S.data,p=d.parameters,z=Math.hypot(p.grid_resistance_ohm,2*Math.PI*p.frequency_hz*p.grid_inductance_h),scr=p.ac_voltage_v**2/(z*150e6);
  $('#case-note').textContent=FAULT_EXPLANATIONS[d.case_id]||`${d.title}. Source: native PSCAD/EMTDC output. ${d.summary.verified_failure_events} verified failures; ${d.summary.inconclusive_events} inconclusive attempts in the analyzed record.`;
  const pairs=[['AC line voltage',`${fmt(p.ac_voltage_v/1000,1)} kV RMS`],['Frequency',`${p.frequency_hz} Hz`],['Firing reference',`${p.alpha_deg}°; event ${p.alpha_event_deg}°`],['DC source magnitude',`${fmt(p.dc_voltage_v/1000,1)} kV`],['DC source event multiplier',fmt(p.dc_step_pu*p.dc_reduce_pu,3)],['Grid R / L',`${p.grid_resistance_ohm} Ω / ${p.grid_inductance_h} H`],['SCR on 150 MW base',fmt(scr,2)],['Per-phase commutation inductance',`${p.commutation_h} H`],['Smoothing reactor',`${p.smoothing_h} H`],['Minimum extinction time',`${p.recovery_us} μs`],['Disturbance',`${fmt(p.fault_start_s,3)}–${fmt(p.fault_start_s+p.fault_duration_s,3)} s`],['Sag magnitude',`${p.sag_pu} pu`],['Fault resistance',`${p.fault_resistance_ohm} Ω`],['Native time step',`${p.time_step_us} μs`]];
  $('#parameters').innerHTML='<table><tbody>'+pairs.map(([a,b])=>`<tr><th>${a}</th><td>${b}</td></tr>`).join('')+'</tbody></table>';
  $('#provenance').textContent=JSON.stringify({source:d.provenance,encoding:d.encoding,quantization_max_abs_error:d.quantization_max_abs_error},null,2);
}
function selectValve(k){S.valve=k;$$('.valve-button').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.valveNumber)===k));if(S.view==='valves')buildPlots();render();}
function pause(){S.playing=false;if($('#play')){$('#play').textContent='Play';$('#play').setAttribute('aria-pressed','false');}}
function bindControls(){
  $('#case-select').addEventListener('change',changeCase);$('#event-select').addEventListener('change',e=>selectEvent(e.target.value));
  $('#play').onclick=()=>{if(!S.data)return;S.playing=!S.playing;$('#play').textContent=S.playing?'Playing':'Play';$('#play').setAttribute('aria-pressed',String(S.playing));};$('#pause').onclick=pause;
  $('#reset').onclick=()=>{pause();setWindow();S.time=S.start;S.guide=0;render();};$('#speed').onchange=e=>S.speed=Number(e.target.value);
  $('#time').oninput=e=>{pause();S.time=S.start+(S.end-S.start)*Number(e.target.value)/10000;render();};
  $('#signal-view').onchange=e=>{S.view=e.target.value;buildPlots();render();};
  $('#compare').onchange=()=>changeReference();$('#reference-select').onchange=()=>changeReference();
  $('#focus-event').onclick=()=>{pause();S.detail=true;setWindow();buildPlots();render();};
  $('#whole-record').onclick=()=>{pause();S.detail=false;setWindow();buildPlots();render();};
  $('#zoom-in').onclick=()=>zoom(.5);$('#zoom-out').onclick=()=>zoom(2);$('#pan-left').onclick=()=>pan(-.3);$('#pan-right').onclick=()=>pan(.3);
  $('#reset-view').onclick=()=>{pause();setWindow();render();};$('#export-plot').onclick=exportPlot;
  $('#previous-step').onclick=()=>guide(-1);$('#next-step').onclick=()=>guide(1);
  $$('.valve-button').forEach(b=>b.onclick=()=>selectValve(Number(b.dataset.valveNumber)));
  $('#enlarge').onclick=()=>{pause();const dialog=$('#diagram-dialog');instantiateCircuit($('#large-circuit'));updateCircuit($('#large-circuit'));dialog.showModal();};$('#close-diagram').onclick=()=>$('#diagram-dialog').close();
  $('#only-failures')?.addEventListener('change',renderTimeline);
  $('#electrical-angle')?.addEventListener('input',e=>{pause();S.time=.52+Number(e.target.value)/360/S.data.parameters.frequency_hz;S.start=.52;S.end=.54;S.detail=false;render();});
  $('#mode')?.addEventListener('click',()=>{pause();document.body.classList.toggle('presentation');const presenting=document.body.classList.contains('presentation');$('#mode').setAttribute('aria-pressed',String(presenting));$('#mode').textContent=presenting?'Study mode':'Presentation mode';$$('.study-copy').forEach(e=>e.style.removeProperty('display'));$('#details-toggle').setAttribute('aria-pressed',String(!presenting));render();});
  $('#details-toggle')?.addEventListener('click',()=>{pause();const show=$('#details-toggle').getAttribute('aria-pressed')!=='true';$('#details-toggle').setAttribute('aria-pressed',String(show));$$('.study-copy').forEach(e=>e.style.setProperty('display',show?'block':'none','important'));});
  $('#level')?.addEventListener('change',e=>{S.level=e.target.value;document.body.classList.remove('level-beginner','level-intermediate','level-advanced');document.body.classList.add('level-'+S.level);});
  document.addEventListener('keydown',e=>{if($('#diagram-dialog').open||/INPUT|SELECT|TEXTAREA|BUTTON/.test(e.target.tagName))return;if(e.code==='Space'){e.preventDefault();$('#play').click();}if(e.key==='ArrowRight'){e.preventDefault();S.time=Math.min(S.end,S.time+S.data.dt);pause();render();}if(e.key==='ArrowLeft'){e.preventDefault();S.time=Math.max(S.start,S.time-S.data.dt);pause();render();}});
  window.addEventListener('resize',()=>render());
}
function zoom(factor){if(!S.data)return;pause();const total=S.data.dt*(S.data.samples-1);const width=Math.max(S.data.dt*8,Math.min(total,(S.end-S.start)*factor));S.start=Math.max(S.data.t0,Math.min(S.time-width/2,S.data.t0+total-width));S.end=S.start+width;render();}
function pan(amount){if(!S.data)return;pause();const width=S.end-S.start;S.start=Math.max(S.data.t0,Math.min(S.start+width*amount,S.data.t0+(S.data.samples-1)*S.data.dt-width));S.end=S.start+width;S.time=Math.max(S.start,Math.min(S.end,S.time));render();}

function chartSpecs(d,e){
  const i=Number(e.incoming.slice(1)),o=Number(e.outgoing.slice(1));
  const field=(key,label,color,scale=1)=>({key,label,color,scale});
  const currents=Array.from({length:6},(_,j)=>field('IT'+(j+1),'T'+(j+1),colors[j],.001));
  const gates=Array.from({length:6},(_,j)=>({...field('G'+(j+1),'T'+(j+1)+' + '+(5-j),colors[j]),offset:5-j}));
  const comm=[field('VT'+o,e.outgoing+' anode–cathode',colors[1],.001),{key:'comm',label:'PCC driving voltage',color:colors[2],scale:.001}];
  if(S.view==='system')return [
    {title:'PCC phase voltages',unit:'kV',series:'ABC'.split('').map((p,j)=>field('VPCC'+p,p,colors[j],.001))},
    {title:'DC current',unit:'kA',series:[field('Idc_meas','DC current',colors[1],.001)]},
    {title:'Bridge DC voltage',unit:'kV',series:[field('Vdc_meas','P minus N',colors[0],.001)]},
    {title:'Transferred power',unit:'MW',series:[field('Pdc_to_bridge','DC into bridge',colors[0],1e-6),field('Pac_to_grid','AC into grid',colors[2],1e-6)]}];
  if(S.view==='gates')return [{title:'Gate commands, vertically offset',unit:'0 / 1 + offset',series:gates},{title:'Measured valve currents',unit:'kA',series:currents}];
  if(S.view==='valves')return [{title:'Six measured valve currents',unit:'kA',series:currents},{title:'Converter phase voltages',unit:'kV',series:'ABC'.split('').map((p,j)=>field('VAC'+p,p,colors[j],.001))},{title:'Selected valve voltage',unit:'kV',series:[field('VT'+S.valve,'T'+S.valve+' anode–cathode',colors[1],.001)]}];
  if(S.view==='angles')return [{title:'Reference angles and valid event measurements',unit:'degrees',series:[field('AlphaRef','α reference',colors[0]),field('Beta','β reference',colors[3]),{key:'gamma',label:'γ valid events only',color:colors[2],scatter:true},{key:'mu',label:'μ completed transfers only',color:colors[4],scatter:true}]},{title:'Measured valve currents',unit:'kA',series:currents}];
  return [{title:`Current transfer: ${e.outgoing} → ${e.incoming}`,unit:'kA',series:[field('IT'+o,e.outgoing+' outgoing',colors[1],.001),field('IT'+i,e.incoming+' incoming',colors[0],.001)]},{title:'Voltage evidence',unit:'kV',series:comm},{title:'Gate commands',unit:'0 / 1',series:[field('G'+i,e.incoming+' incoming',colors[0]),field('G'+o,e.outgoing+' outgoing',colors[1])]}];
}
function seriesValue(d,e,s,k){
  let v;
  if(s.key==='comm'){const i=Number(e.incoming.slice(1)),o=Number(e.outgoing.slice(1));v=(i%2?1:-1)*(d.signals['VPCC'+phase[i]][k]-d.signals['VPCC'+phase[o]][k]);}
  else if(s.key==='Beta')v=180-d.signals.AlphaRef[k];else v=d.signals[s.key]?.[k];
  return v*(s.scale??1)+(s.offset??0);
}
function referenceOffset(){return S.detail&&S.refEvent?S.refEvent.time_s-S.event.time_s:0;}
function buildPlots(){
  if(!S.data||!S.event)return;
  for(const [id,d,e] of [['primary-plots',S.data,S.event],['reference-plots',S.reference,S.refEvent]]){
    const root=$('#'+id);root.innerHTML='';if(!d||!e)continue;
    chartSpecs(d,e).forEach((spec,j)=>{
      const el=document.createElement('div');el.className='plot-panel';el.innerHTML=`<canvas role="img" aria-label="${escapeText(spec.title)}"></canvas><div class="legend">${spec.series.map(s=>`<span><i style="border-color:${s.color}"></i>${escapeText(s.label)}</span>`).join('')}</div>`;
      const canvas=$('canvas',el);canvas.dataset.chart=j;canvas.dataset.reference=id.startsWith('reference')?'1':'0';
      const move=ev=>{if(ev.type==='pointermove'&&!ev.buttons)return;pause();const rect=canvas.getBoundingClientRect(),left=58,right=14;const fraction=Math.max(0,Math.min(1,(ev.clientX-rect.left-left)/(rect.width-left-right)));S.time=S.start+fraction*(S.end-S.start);render();};
      canvas.addEventListener('pointerdown',ev=>{canvas.setPointerCapture(ev.pointerId);move(ev);});canvas.addEventListener('pointermove',move);root.append(el);
    });
  }
}
function bounds(d,e,spec,start,end){
  let lo=0,hi=0;const a=indexAt(d,start),b=indexAt(d,end);
  for(const s of spec.series){
    if(s.scatter){for(const ev of d.events){if(ev.time_s<start||ev.time_s>end)continue;const v=ev[s.key==='gamma'?'gamma_deg':'overlap_deg'];if(v!==null&&Number.isFinite(v)){lo=Math.min(lo,v);hi=Math.max(hi,v);}}}
    else for(let k=a;k<=b;k++){const v=seriesValue(d,e,s,k);if(Number.isFinite(v)){lo=Math.min(lo,v);hi=Math.max(hi,v);}}
  }
  if(hi-lo<.01)hi=lo+1;return [lo,hi];
}
function drawPlot(canvas,d,e,spec,start,end,cursor,range){
  const width=Math.max(270,canvas.getBoundingClientRect().width),height=210,ratio=Math.min(2,window.devicePixelRatio||1);
  if(canvas.width!==Math.round(width*ratio)||canvas.height!==height*ratio){canvas.width=Math.round(width*ratio);canvas.height=height*ratio;}
  const ctx=canvas.getContext('2d');ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,width,height);ctx.fillStyle='#fff';ctx.fillRect(0,0,width,height);
  const left=58,right=14,top=34,bottom=34,pw=width-left-right,ph=height-top-bottom;
  let [ymin,ymax]=range;const margin=(ymax-ymin)*.08;ymin-=margin;ymax+=margin;
  const X=t=>left+(t-start)/(end-start)*pw,Y=v=>top+(ymax-v)/(ymax-ymin)*ph;
  ctx.font='600 12px Segoe UI, Arial';ctx.fillStyle='#183c50';ctx.fillText(spec.title,10,16);ctx.font='10px Segoe UI, Arial';ctx.fillStyle='#526d7e';ctx.fillText(spec.unit,10,29);
  ctx.lineWidth=1;ctx.strokeStyle='#e4edf1';ctx.textAlign='right';
  for(let j=0;j<=4;j++){const v=ymin+(ymax-ymin)*j/4,y=Y(v);ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(width-right,y);ctx.stroke();ctx.fillText(Math.abs(v)>=100?v.toFixed(0):v.toFixed(1),left-7,y+3);}
  ctx.textAlign='center';
  for(let j=0;j<=4;j++){const t=start+(end-start)*j/4,x=X(t);ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,height-bottom);ctx.stroke();ctx.fillText(S.detail?((t-e.time_s)*1000).toFixed(1):t.toFixed(3),x,height-bottom+15);}
  ctx.fillText(S.detail?'Time relative to firing (ms)':'Time (s)',left+pw/2,height-3);
  ctx.save();ctx.beginPath();ctx.rect(left,top,pw,ph);ctx.clip();
  const fp=d.parameters;ctx.fillStyle='#d6a33d18';ctx.fillRect(X(fp.fault_start_s),top,X(fp.fault_start_s+fp.fault_duration_s)-X(fp.fault_start_s),ph);
  for(const time of [e.time_s,e.current_completion_s,e.failure_time_s,e.reverse_bias_end_s]){if(time==null)continue;ctx.setLineDash([3,4]);ctx.strokeStyle=time===e.failure_time_s?'#b43b30':'#8396a1';ctx.beginPath();ctx.moveTo(X(time),top);ctx.lineTo(X(time),height-bottom);ctx.stroke();}ctx.setLineDash([]);
  for(const s of spec.series){
    ctx.strokeStyle=s.color;ctx.fillStyle=s.color;ctx.lineWidth=1.7;
    if(s.scatter){for(const ev of d.events){if(ev.time_s<start||ev.time_s>end)continue;const v=ev[s.key==='gamma'?'gamma_deg':'overlap_deg'];if(v==null)continue;ctx.beginPath();ctx.arc(X(ev.time_s),Y(v),2.7,0,Math.PI*2);ctx.fill();}continue;}
    const a=indexAt(d,start),b=indexAt(d,end),stride=Math.max(1,Math.floor((b-a)/(pw*1.5)));ctx.beginPath();let first=true;
    const point=k=>{const v=seriesValue(d,e,s,k);if(!Number.isFinite(v))return;const x=X(d.t0+k*d.dt),y=Y(v);if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);};
    for(let k=a;k<=b;k+=stride){
      if(stride===1){point(k);continue;}let mn=k,mx=k;for(let j=k+1;j<=Math.min(b,k+stride-1);j++){if(seriesValue(d,e,s,j)<seriesValue(d,e,s,mn))mn=j;if(seriesValue(d,e,s,j)>seriesValue(d,e,s,mx))mx=j;}point(Math.min(mn,mx));if(mn!==mx)point(Math.max(mn,mx));
    }point(b);ctx.stroke();
  }
  ctx.strokeStyle='#173c53';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(X(cursor),top);ctx.lineTo(X(cursor),height-bottom);ctx.stroke();
  ctx.restore();ctx.textAlign='left';
}
function renderPlots(){
  const a=chartSpecs(S.data,S.event),b=S.compare&&S.reference?chartSpecs(S.reference,S.refEvent):[],offset=referenceOffset();
  const primary=$$('#primary-plots canvas'),secondary=$$('#reference-plots canvas');
  a.forEach((spec,j)=>{
    let range=bounds(S.data,S.event,spec,S.start,S.end);
    if(S.compare&&b[j]){const q=bounds(S.reference,S.refEvent,b[j],S.start+offset,S.end+offset);range=[Math.min(range[0],q[0]),Math.max(range[1],q[1])];}
    if(primary[j])drawPlot(primary[j],S.data,S.event,spec,S.start,S.end,S.time,range);
    if(S.compare&&secondary[j]&&b[j])drawPlot(secondary[j],S.reference,S.refEvent,b[j],S.start+offset,S.end+offset,S.time+offset,range);
  });
  $('#primary-name').textContent=S.data.case_id+' · '+S.data.title;
  if(S.reference)$('#reference-name').textContent=S.reference.case_id+' · '+S.reference.title;
  $('#alignment-note').textContent=S.compare?(S.detail?'Recordings aligned at the selected incoming firing. Both columns use the same horizontal interval and vertical scales.':'Recordings aligned by absolute simulation time. Both columns use the same horizontal interval and vertical scales.'):'All plots and circuit highlights share the same recorded time cursor.';
}
function updateCircuit(container){
  if(!container||!S.data)return;const d=S.data,t=S.time,threshold=Math.max(1,.001*Math.abs(value(d,'Idc_meas',t)));
  for(let k=1;k<=6;k++){
    const el=$(`[data-valve="T${k}"]`,container);if(!el)continue;const on=value(d,'IT'+k,t)>threshold;
    el.classList.toggle('on',on);el.classList.toggle('incoming',on&&S.event.incoming==='T'+k);el.classList.toggle('outgoing',on&&S.event.outgoing==='T'+k);el.classList.toggle('picked',S.valve===k);
  }
  $('[data-part="dc-path"]',container)?.classList.toggle('active',Math.abs(value(d,'Idc_meas',t))>threshold);
  for(const [p,u,l] of [['A',1,4],['B',3,6],['C',5,2]])$(`[data-part="phase-${p}"]`,container)?.classList.toggle('active',Math.abs(value(d,'IT'+u,t)-value(d,'IT'+l,t))>threshold);
}
function render(){
  if(!S.data||!S.event)return;S.time=Math.max(S.data.t0,Math.min(S.data.t0+(S.data.samples-1)*S.data.dt,S.time));
  const d=S.data,t=S.time,e=S.event;$('#time-value').textContent=fmt(t,5)+' s';$('#time').value=String(Math.round((t-S.start)/(S.end-S.start)*10000));
  $('#reading-current').textContent=fmt(value(d,'Idc_meas',t)/1000,3)+' kA';$('#reading-voltage').textContent=fmt(value(d,'Vdc_meas',t)/1000,1)+' kV';$('#reading-power').textContent=fmt(value(d,'Pdc_to_bridge',t)/1e6,1)+' MW';
  $('#reading-class').innerHTML=`<span class="badge ${badge(e)}">${readable(e.classification)}</span>`;
  const threshold=Math.max(1,.001*Math.abs(value(d,'Idc_meas',t)));
  $$('.valve-button').forEach(b=>{const k=Number(b.dataset.valveNumber),i=value(d,'IT'+k,t),g=value(d,'G'+k,t)>.5;b.classList.toggle('on',i>threshold);$('small',b).textContent=`${i>threshold?'ON':'OFF'} · gate ${g?'1':'0'} · ${fmt(i/1000,2)} kA`;});
  $('#valve-info').textContent=`Selected T${S.valve}: ${fmt(value(d,'IT'+S.valve,t),1)} A; anode–cathode ${fmt(value(d,'VT'+S.valve,t)/1000,2)} kV. ${S.valve%2?'Upper':'Lower'} group, phase ${phase[S.valve]}. ON display threshold: ${fmt(threshold,1)} A; gate command is separate.`;
  updateCircuit($('#circuit'));if($('#diagram-dialog').open)updateCircuit($('#large-circuit'));
  $('#value-inspector').textContent=`Cursor ${fmt(t,5)} s | ${e.outgoing}: ${fmt(value(d,'I'+e.outgoing,t)/1000,3)} kA | ${e.incoming}: ${fmt(value(d,'I'+e.incoming,t)/1000,3)} kA | α reference ${fmt(value(d,'AlphaRef',t),1)}°`;
  $('#event-evidence').innerHTML=`<p><strong>${e.event_id}: ${e.outgoing} → ${e.incoming}</strong> · firing at ${fmt(e.time_s,5)} s · ${e.verified_failure?'verified failure':'not counted as a verified failure'}</p><ul>${e.evidence.map(x=>'<li>'+escapeText(x)+'</li>').join('')}</ul><p>Measured overlap: ${e.overlap_deg==null?'not established':fmt(e.overlap_deg,2)+'°'}. Valid reverse-bias interval: ${e.gamma_deg==null?'not established':fmt(e.gamma_deg,2)+'°'}. ${e.abnormal_sequence?'The actual outgoing valve differs from the normal sequence.':''}</p><p class="advanced advanced-only">Detector detail: current off threshold ${fmt(e.current_threshold_A,1)} A; observed window ends at ${fmt(e.window_end_s,5)} s. Three consecutive samples establish each sustained condition. These thresholds belong to the event detector, independently of the circuit ON display.</p>`;
  if($('#electrical-angle')){$('#angle-value').textContent=fmt(((t-.52)*d.parameters.frequency_hz*360%360+360)%360,1)+'°';}
  renderGuide();renderPlots();
}
function guidePoints(){
  const e=S.event,zero=e.current_completion_s??Math.min(e.window_end_s,e.time_s+.002),end=e.reverse_bias_end_s??Math.min(e.window_end_s,e.time_s+.004);
  return [e.time_s-.0004,e.time_s+S.data.dt,(e.time_s+zero)/2,zero+S.data.dt,(zero+end)/2,end+S.data.dt];
}
function renderGuide(){
  const failed=S.event.verified_failure;const titles=['Start with the outgoing valve','Apply the incoming gate','Inspect the current transfer',failed?'Check whether current extinguishes':'Complete the transfer',failed?'Look for reverse voltage':'Observe reverse bias','Assess the outcome'];
  const texts=[`${S.event.outgoing} is the outgoing valve for this measured attempt. Its current establishes the initial conduction state.`,`${S.event.incoming} receives a gate command. The command alone does not prove that it takes over the current.`,`${S.event.incoming} and ${S.event.outgoing} can share current during overlap. Follow both measured curves.`,failed?'Inspect the outgoing current carefully. In an unsuccessful transfer it never reaches zero; in resumed conduction it reaches zero and then returns.':`Inspect the outgoing-current threshold crossing and the subsequent sustained reverse voltage. Measured overlap ends only when reverse-voltage evidence confirms extinction; missing evidence remains inconclusive.`,failed?'A conducting valve has only a small on-state voltage. It cannot establish a sustained reverse-bias interval while it continues carrying positive current.':'After current extinction, negative anode-to-cathode voltage provides a recovery interval. Measure its duration up to the return of forward voltage.',failed?'The classification combines current transfer and valve voltage evidence. DC current rise or low voltage alone would be insufficient.':`This attempt is ${readable(S.event.classification)}. A smaller valid extinction interval does not by itself prove failure.`];
  if(S.event.classification==='inconclusive'){titles[3]='Check the missing evidence';texts[3]=S.event.evidence.join(' ');titles[4]='Do not assume recovery';texts[4]='This attempt does not establish all required current and voltage conditions. Guided cursor positions are inspection points, not measured interval boundaries.';}
  $('#guide-count').textContent=`Step ${S.guide+1} of 6`;$('#guide-title').textContent=titles[S.guide];$('#guide-text').textContent=texts[S.guide];$('#previous-step').disabled=S.guide===0;$('#next-step').disabled=S.guide===5;
}
function guide(delta){pause();S.guide=Math.max(0,Math.min(5,S.guide+delta));S.time=Math.max(S.start,Math.min(S.end,guidePoints()[S.guide]));render();}
function renderTimeline(){
  if(!$('#timeline')||!S.data)return;const sum=S.data.summary;
  $('#timeline-summary').textContent=`${sum.verified_failure_events} verified failures; ${sum.inconclusive_events} inconclusive attempts. ${sum.post_clearing_failure_events??'Not yet classified'} failures occur after clearing; ${sum.subsequent_failure_events??0} meet the stated recovery-then-recurrence criterion.`;
  const events=$('#only-failures').checked?S.data.events.filter(e=>e.verified_failure):S.data.events;
  $('#timeline').innerHTML=events.map(e=>`<button data-event="${e.event_id}" class="${e.verified_failure?'failure':e.classification==='inconclusive'?'inconclusive':'normal'} ${e.event_id===S.event.event_id?'selected':''}" title="${escapeText(e.outgoing+' to '+e.incoming+': '+readable(e.classification))}">${e.event_id} · ${fmt(e.time_s,3)} s<br>${e.outgoing} → ${e.incoming}</button>`).join('');
  $$('[data-event]',$('#timeline')).forEach(b=>b.onclick=()=>selectEvent(b.dataset.event));
}
function exportPlot(){
  pause();const canvases=$$('#primary-plots canvas');const out=document.createElement('canvas');out.width=1200;out.height=70+canvases.length*350;const ctx=out.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,out.width,out.height);ctx.fillStyle='#183c50';ctx.font='22px Arial';ctx.fillText(`${S.data.case_id} / ${S.event.event_id} — Actual PSCAD recording`,30,35);canvases.forEach((c,j)=>ctx.drawImage(c,0,70+j*350,1200,350));const a=document.createElement('a');a.href=out.toDataURL('image/png');a.download=`${S.data.case_id}_${S.event.event_id}.png`;a.click();
}
const QUESTIONS=[
 {q:'Which is the normal firing sequence?',a:['T1 → T2 → T3 → T4 → T5 → T6','T1 → T3 → T5 → T2 → T4 → T6','All six valves simultaneously'],ok:0,why:'The numbering follows the six 60° firing intervals. Upper and lower groups alternate.'},
 {q:'The incoming valve is T5 in normal operation. Which upper-group valve is outgoing?',a:['T2','T3','T6'],ok:1,why:'The upper group follows T1 → T3 → T5. T3 transfers current to T5.'},
 {q:'What turns off an already conducting thyristor in this LCC?',a:['Removing its gate command alone','A negative gate command','Current extinction followed by sufficient recovery conditions'],ok:2,why:'An LCC thyristor is line commutated. The network transfers its current, and reverse bias supports recovery.'},
 {q:'What is the strongest evidence of unsuccessful current transfer?',a:['DC voltage has fallen','Outgoing current persists while incoming current rises and then falls; outgoing reverse bias is absent','The firing-angle reference changed'],ok:1,why:'The valve-level current and voltage evidence directly establishes the failed transfer.'},
 {q:'A recording has a 12.6° extinction interval and completed current transfer. What can be concluded?',a:['Failure is proved by the low angle','Reduced margin is observed; failure is not proved','The converter must have blocked'],ok:1,why:'CF-01 is a measured example with reduced margin and no verified failure.'},
 {q:'If α = 140° and μ = 11.2° under the stated sinusoidal convention, what is γ in degrees?',numeric:28.8,why:'γ = 180° − α − μ = 28.8°. This equation does not replace valve-level measurements during a disturbance.'},
 {q:'At 50 Hz, a reverse-bias interval of 1.6 ms corresponds to how many electrical degrees?',numeric:28.8,why:'γ = 360 f Δt = 360 × 50 × 0.0016 = 28.8°.'},
 {q:'Does a failure occurring after fault clearing automatically prove a subsequent failure after recovery?',a:['Yes, clearing guarantees recovery','No; the recovery sequence must be established','Yes, if DC current is high'],ok:1,why:'Persistent failure can continue after clearing. This laboratory requires six consecutive successful attempts before labeling recurrence.'},
 {q:'Which statement describes the browser parameter controls?',a:['They run a complete EMT solver','They select recorded PSCAD operating points','They interpolate arbitrary transients and treat them as PSCAD output'],ok:1,why:'Each selected operating point has its own executed model, native file hashes, and event evidence.'},
 {q:'How should mitigation be assessed?',a:['Using the failure count alone','Using current reduction alone','Using failure evidence, current, voltage, recovery, and power under comparable conditions'],ok:2,why:'A lower failure count may accompany reduced power or interrupted conduction. Those tradeoffs belong in the conclusion.'}
];
function buildAssessment(){
  $('#assessment').innerHTML='<h2>Knowledge assessment</h2><p>Use the recording above to support your reasoning. Each question explains the result.</p>'+QUESTIONS.map((q,j)=>`<div class="question" data-question="${j}"><h3>${j+1}. ${q.q}</h3>${q.numeric!=null?`<label for="answer-${j}">Answer in degrees</label> <input id="answer-${j}" type="number" step="0.1" aria-label="Question ${j+1}: numerical answer">`:`<div class="answers">${q.a.map((a,k)=>`<label><input type="radio" name="q${j}" value="${k}">${a}</label>`).join('')}</div>`}<button class="check-answer" data-check="${j}">Check answer</button><p class="feedback" aria-live="polite"></p></div>`).join('')+'<div class="assessment-tools"><button id="grade" class="primary">Score assessment</button><button id="reset-exercises">Reset exercises</button><output id="score" class="score" aria-live="polite"></output></div>';
  $$('[data-check]').forEach(b=>b.onclick=()=>checkAnswer(Number(b.dataset.check)));
  $('#grade').onclick=()=>{let score=0;QUESTIONS.forEach((q,j)=>{if(checkAnswer(j))score++;});$('#score').textContent=`${score} / ${QUESTIONS.length} correct`;};
  $('#reset-exercises').onclick=()=>{$$('#assessment input').forEach(i=>{i.checked=false;if(i.type==='number')i.value='';});$$('.feedback').forEach(e=>{e.textContent='';e.className='feedback';});$('#score').textContent='';};
  const practice=document.createElement('section');practice.className='card';practice.innerHTML='<h2>Waveform and circuit practice</h2><p>Inspect the selected recording above. Start a task, click a valve in the circuit or its labeled button, then check your selection.</p><button id="practice-outgoing">Identify the outgoing valve</button> <button id="practice-incoming">Identify the incoming valve</button><p id="valve-practice-prompt">Start a task to inspect the selected firing attempt.</p><button id="check-valve-practice">Check selected valve</button><p id="valve-practice-feedback" class="feedback" aria-live="polite"></p><p><strong>Overlap task:</strong> focus a successful event and move the cursor through the interval where the incoming and outgoing currents are both positive. Then use the guided steps to check the measured current-extinction marker.</p><label for="waveform-diagnosis">Interpret the selected valve waveforms</label> <select id="waveform-diagnosis"><option value="">Choose an interpretation</option><option value="normal">Successful transfer or reduced margin</option><option value="failure">Verified failed transfer</option><option value="inconclusive">Insufficient evidence</option></select> <button id="check-waveform">Check interpretation</button><p id="waveform-feedback" class="feedback" aria-live="polite"></p>';
  $('#assessment').before(practice);let target=null;
  for(const kind of ['outgoing','incoming'])$('#practice-'+kind).onclick=()=>{pause();target=kind;$('#valve-practice-prompt').textContent=`Select the ${kind} valve for ${S.data.case_id} / ${S.event.event_id}. Use the currents at the firing instant.`;$('#valve-practice-feedback').textContent='';};
  $('#check-valve-practice').onclick=()=>{const out=$('#valve-practice-feedback');if(!target){out.textContent='Start a valve-identification task first.';return;}const correct='T'+S.valve===S.event[target];out.className='feedback '+(correct?'correct':'incorrect');out.textContent=(correct?'Correct. ':'Try again. ')+`${S.event[target]} is ${target} in this measured attempt. The incoming current rises after its gate, while the outgoing valve initially carries the current.`;};
  $('#check-waveform').onclick=()=>{const want=S.event.verified_failure?'failure':S.event.classification==='inconclusive'?'inconclusive':'normal',choice=$('#waveform-diagnosis').value;$('#waveform-feedback').textContent=!choice?'Choose an interpretation first.':(choice===want?'Correct. ':'Try again. ')+S.event.evidence.join(' ');};
}
function checkAnswer(j){
  const q=QUESTIONS[j],row=$(`[data-question="${j}"]`),out=$('.feedback',row);let answered=false,correct=false;
  if(q.numeric!=null){const input=$('input',row);answered=input.value.trim()!=='';correct=answered&&Math.abs(Number(input.value)-q.numeric)<=.2;}else{const input=$('input:checked',row);answered=!!input;correct=answered&&Number(input.value)===q.ok;}
  out.className='feedback '+(correct?'correct':'incorrect');out.textContent=!answered?'Choose or enter an answer first.':(correct?'Correct. ':'Try again. ')+q.why;return correct;
}
let lastFrame=0;
function tick(now){
  if(S.playing&&S.data){const elapsed=Math.min(.1,(now-lastFrame)/1000);S.time+=elapsed*S.speed/S.data.parameters.frequency_hz;if(S.time>S.end)S.time=S.start;render();}lastFrame=now;requestAnimationFrame(tick);
}
buildPage();requestAnimationFrame(tick);
