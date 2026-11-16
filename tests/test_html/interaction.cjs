/* User-visible integration checks against the actual offline recordings. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
let chromium; try { ({chromium}=require('playwright')); } catch { ({chromium}=require('../../.local/web/node_modules/playwright')); }
const root=path.resolve(__dirname,'../..');
const base=process.env.LAB_URL || 'http://127.0.0.1:8765/';
const results=[];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
 const errors=[]; page.on('pageerror',e=>errors.push(String(e))); page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
 async function ready(){await page.locator('#load-status').waitFor({state:'hidden',timeout:30000});}
 async function check(name,fn){await fn();results.push(name);console.log('PASS',name);}
 try {
 await page.goto(base+'modules/01_lcc_inverter_fundamentals.html');await ready();
 await check('Selected valve changes waveform legend',async()=>{await page.locator('[data-valve-number="4"]').click();assert.match(await page.locator('#primary-plots .legend').last().innerText(),/T4 anode/);});
 await check('Presentation mode pauses and preserves selections',async()=>{
   await page.locator('#details-toggle').click();await page.locator('#details-toggle').click();
   const val=await page.locator('#case-select').inputValue();await page.locator('#play').click();await page.locator('#mode').click();
   assert.equal(await page.locator('#case-select').inputValue(),val);assert.equal(await page.locator('#play').getAttribute('aria-pressed'),'false');
   assert.equal(await page.locator('.study-copy').first().isVisible(),false);await page.locator('#mode').click();assert.equal(await page.locator('.study-copy').first().isVisible(),true);
 });
 const files=fs.readdirSync(path.join(root,'docs/modules')).filter(x=>x.endsWith('.html'));
 for(const file of ['index.html',...files.map(f=>'modules/'+f)]){
  await check(file+' desktop controls',async()=>{
   await page.goto(base+file);await ready();assert.equal(await page.locator('#circuit [data-valve]').count(),6);
   const before=await page.locator('#time-value').innerText();await page.locator('#play').click();await page.waitForTimeout(200);await page.locator('#pause').click();assert.notEqual(await page.locator('#time-value').innerText(),before);
   await page.locator('#time').fill('7000');assert.notEqual(await page.locator('#time-value').innerText(),before);
   for(const id of ['reset','whole-record','zoom-in','zoom-out','pan-right','pan-left','reset-view','focus-event','next-step','previous-step'])await page.locator('#'+id).click();
   for(const view of ['system','valves','gates','angles','commutation']){await page.locator('#signal-view').selectOption(view);assert.ok(await page.locator('#primary-plots canvas').count()>0);}
   await page.locator('#speed').selectOption('2');await page.locator('#enlarge').click();assert.equal(await page.locator('#diagram-dialog').isVisible(),true);await page.locator('#close-diagram').click();
   const downloadPromise=page.waitForEvent('download');await page.locator('#export-plot').click();const download=await downloadPromise;assert.match(download.suggestedFilename(),/\.png$/);assert.ok(fs.statSync(await download.path()).size>1000);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  });
  await check(file+' mobile layout',async()=>{await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.locator('#circuit').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,'.local/mobile-'+path.basename(file)+'.png')});await page.setViewportSize({width:1440,height:1000});});
 }
 await check('Rendered equations and recorded case selection',async()=>{
  await page.goto(base+'modules/02_commutation_and_extinction_angle.html');await ready();assert.ok(await page.locator('.katex').count()>0);
  await page.locator('#case-select').selectOption('CF-01');await ready();assert.match(await page.locator('#primary-name').innerText(),/CF-01/);
 });
 await check('Timeline filters and selects real events',async()=>{
  await page.goto(base+'modules/05_repeated_commutation_failures.html');await ready();await page.locator('#only-failures').check();assert.equal(await page.locator('#timeline .inconclusive').count(),0);const button=page.locator('#timeline button').last();const id=await button.getAttribute('data-event');await button.click();assert.equal(await page.locator('#event-select').inputValue(),id);
 });
 await check('Every exported case loads its own recording',async()=>{
  await page.goto(base+'modules/06_parameters_and_mitigation.html');await ready();
  const ids=await page.locator('#case-select option').evaluateAll(options=>options.map(o=>o.value));
  for(const id of ids){await page.locator('#case-select').selectOption(id);await ready();assert.ok((await page.locator('#primary-name').innerText()).startsWith(id+' ·'));}
 });
 await check('Circuit conduction agrees with selected native CSV samples',async()=>{
  await page.goto(base+'modules/01_lcc_inverter_fundamentals.html');await ready();
  const event=JSON.parse(fs.readFileSync(path.join(root,'results/validated_samples/CF-00_event.json'),'utf8'));
  await page.locator('#event-select').selectOption(event.event_id);await page.locator('#time').fill('6000');
  const t=Number((await page.locator('#time-value').innerText()).split(' ')[0]);const rows=fs.readFileSync(path.join(root,'results/validated_samples/CF-00_event.csv'),'utf8').trim().split(/\r?\n/).map(x=>x.split(','));const headers=rows.shift();const sample=rows.find(r=>Math.abs(Number(r[0])-t)<1e-7);assert.ok(sample);
  const v=key=>Number(sample[headers.indexOf(key)]),threshold=Math.max(1,.001*Math.abs(v('Idc_meas')));
  for(let k=1;k<=6;k++){const button=page.locator(`[data-valve-number="${k}"]`);const on=/\bON\b/.test(await button.innerText());assert.equal(on,v('IT'+k)>threshold,'T'+k);}
  await page.locator('#level').selectOption('intermediate');assert.equal(await page.locator('#event-evidence .advanced-only').isVisible(),false);await page.locator('#level').selectOption('advanced');assert.equal(await page.locator('#event-evidence .advanced-only').isVisible(),true);
 });
 await check('Quiz feedback, scoring, reset and graphical selection',async()=>{
  await page.goto(base+'modules/07_interactive_exercises.html');await ready();await page.locator('[data-check="0"]').click();assert.match(await page.locator('[data-question="0"] .feedback').innerText(),/Choose/);
  for(const [i,v] of [[0,0],[1,1],[2,2],[3,1],[4,1],[7,1],[8,1],[9,2]])await page.locator(`input[name=q${i}][value="${v}"]`).check();
  await page.locator('#answer-5').fill('28.8');await page.locator('#answer-6').fill('28.8');await page.locator('#grade').click();assert.equal(await page.locator('#score').innerText(),'10 / 10 correct');await page.locator('#reset-exercises').click();assert.equal(await page.locator('#score').innerText(),'');
  await page.locator('#practice-outgoing').click();await page.locator('[data-valve-number="5"]').click();await page.locator('#check-valve-practice').click();assert.match(await page.locator('#valve-practice-feedback').innerText(),/Correct/);
 });
 await check('Direct file opening without a local server',async()=>{await page.goto(pathToFileURL(path.join(root,'docs/modules/03_normal_vs_failed_commutation.html')).href);await ready();assert.match(await page.locator('#primary-name').innerText(),/CF-02/);assert.match(await page.locator('#reference-name').innerText(),/CF-00/);});
 assert.deepEqual(errors,[]);results.push('No browser errors or failed HTTP assets');
 } finally {
  fs.mkdirSync(path.join(root,'reports'),{recursive:true});fs.writeFileSync(path.join(root,'reports/browser_tests.json'),JSON.stringify({completed_at:new Date().toISOString(),passed:results,errors},null,2));await browser.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
