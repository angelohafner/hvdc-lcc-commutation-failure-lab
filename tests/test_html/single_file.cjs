/* Open only the delivered HTML in an isolated folder, with networking disabled. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const crypto=require('node:crypto'),zlib=require('node:zlib'),{pathToFileURL}=require('node:url');
let chromium;try{({chromium}=require('playwright'));}catch{({chromium}=require('../../.local/web/node_modules/playwright'));}
const root=path.resolve(__dirname,'../..'),source=path.join(root,'dist/HVDC_LCC_Virtual_Laboratory.html');
const results=[],errors=[],blocked=[];
(async()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'hvdc-single-file-')),file=path.join(folder,'Virtual_Lab.html');fs.copyFileSync(source,file);
 const url=pathToFileURL(file).href,browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const context=await browser.newContext({offline:true,viewport:{width:1440,height:1000},acceptDownloads:true});
 await context.route('**/*',route=>{const u=route.request().url();if(u.startsWith('data:')||u.startsWith('blob:')||u.startsWith('about:')||u.split('#')[0]===url)return route.continue();blocked.push(u);return route.abort();});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 async function check(name,fn){await fn();results.push(name);console.log('PASS',name);}
 async function frame(id){const locator=page.locator('#module-frame-'+id);await locator.waitFor({state:'visible'});const f=await (await locator.elementHandle()).contentFrame();await f.locator(id==='report'?'h1':'#case-select').waitFor();if(id!=='report')await f.locator('#load-status').waitFor({state:'hidden',timeout:45000});return f;}
 async function go(id){await page.locator('#module-switch').selectOption(String(id));return frame(String(id));}
 try{
  await page.goto(url,{timeout:60000});await frame('0');
  await check('One isolated HTML opens offline with no companion files',async()=>{assert.deepEqual(fs.readdirSync(folder),['Virtual_Lab.html']);assert.equal(await page.locator('#module-switch option').count(),9);assert.match(await page.title(),/Single-file/);});
  await check('Skip-to-laboratory link moves keyboard focus past repeated navigation',async()=>{const f=await go(1);await f.locator('a.skip').focus();await f.locator('a.skip').press('Enter');await page.keyboard.press('Tab');assert.equal(await f.evaluate(()=>document.activeElement.id),'case-select');});
  await check('Printing retains the complete technical report',async()=>{await go('report');const pdf=await page.pdf({path:path.join(root,'.local/single-file-report-print.pdf'),format:'A4',printBackground:true});const pages=(pdf.toString('latin1').match(/\/Type\s*\/Page\b/g)||[]).length;assert.ok(pages>10&&pages<40,'Complete report page count: '+pages);assert.equal(await page.locator('#module-switch').isVisible(),true);});
  for(let i=0;i<8;i++){
   await check('Module '+i+' playback, controls, plots and diagram',async()=>{
    const f=await go(i);assert.equal(await f.locator('#circuit [data-valve]').count(),6);
    const before=await f.locator('#time-value').innerText();await f.locator('#play').click();await f.waitForFunction(value=>document.querySelector('#time-value').innerText!==value,before,{timeout:5000});await f.locator('#pause').click();assert.notEqual(await f.locator('#time-value').innerText(),before);
    await f.locator('#time').fill('6000');for(const id of ['zoom-in','zoom-out','pan-left','pan-right','reset-view','whole-record','focus-event','next-step','previous-step','reset'])await f.locator('#'+id).click();
    for(const view of ['system','valves','gates','angles','commutation']){await f.locator('#signal-view').selectOption(view);assert.ok(await f.locator('#primary-plots canvas').count()>0);}
    await f.locator('#speed').selectOption('2');await f.locator('#enlarge').click();assert.equal(await f.locator('#diagram-dialog').isVisible(),true);
    const rect=await f.locator('#diagram-dialog').boundingBox();assert.ok(rect.y>=0&&rect.y+rect.height<=1000);await f.locator('#close-diagram').click();
    assert.equal(await f.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   });
   await check('Module '+i+' mobile layout and visible dialog',async()=>{
    await page.setViewportSize({width:390,height:844});const f=await frame(String(i));assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.equal(await f.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await f.locator('#enlarge').click();const box=await f.locator('#diagram-dialog').boundingBox();assert.ok(box.x>=0&&box.x+box.width<=391&&box.y>=0&&box.y+box.height<=845);await f.locator('#close-diagram').click();
    if(i===0)await page.screenshot({path:path.join(root,'.local/single-file-mobile.png')});await page.setViewportSize({width:1440,height:1000});
   });
  }
  await check('Module navigation pauses playback and retains cursor, view and valve',async()=>{
   let f=await go(1);await f.locator('#signal-view').selectOption('valves');await f.locator('[data-valve-number="4"]').click();await f.locator('#time').fill('6500');await f.locator('#level').selectOption('advanced');
   await f.locator('#play').click();await go(2);assert.equal(await f.locator('#play').getAttribute('aria-pressed'),'false');const time=await f.locator('#time-value').innerText();await page.waitForTimeout(150);assert.equal(await f.locator('#time-value').innerText(),time);f=await go(1);assert.equal(await f.locator('#time-value').innerText(),time);assert.equal(await f.locator('#signal-view').inputValue(),'valves');assert.equal(await f.locator('#level').inputValue(),'advanced');assert.equal(await f.locator('[data-valve-number="4"]').getAttribute('aria-pressed'),'true');
   await f.locator('#mode').click();assert.equal(await f.locator('.study-copy').first().isVisible(),false);await f.locator('#details-toggle').click();assert.equal(await f.locator('.study-copy').first().isVisible(),true);await f.locator('#mode').click();assert.equal(await f.locator('#time-value').innerText(),time);
  });
  await check('Internal links, browser history and report anchors stay in this file',async()=>{
   const f=await go(0);await f.locator('a.module-link[href*="03_normal"]').click();await frame('3');assert.ok(page.url().endsWith('#3'));await page.goBack();await frame('0');await page.goForward();await frame('3');
   const report=await go('report');assert.ok(await report.locator('img').count()>5);await report.locator('a[href="#case-CF-02"]').first().click();assert.equal(report.url(),'about:srcdoc');assert.ok(page.url().startsWith(url));
   const images=await report.locator('img').evaluateAll(images=>images.every(i=>i.complete&&i.naturalWidth>0&&i.src.startsWith('data:')));assert.equal(images,true);assert.equal(await report.locator('.katex').count(),await report.locator('.math').count());assert.equal(await report.locator('.math').count(),5);
  });
  await check('Embedded mathematical fonts render without network access',async()=>{const f=await go(2);await f.evaluate(()=>document.fonts.ready);const loaded=await f.evaluate(()=>[...document.fonts].filter(x=>x.status==='loaded').map(x=>x.family));assert.ok(loaded.some(x=>x.includes('KaTeX')));assert.ok(await f.locator('.katex').count()>0);});
  await check('Quiz scores, graphical valve tasks and answers survive module navigation',async()=>{
   let f=await go(7);for(const [i,v] of [[0,0],[1,1],[2,2],[3,1],[4,1],[7,1],[8,1],[9,2]])await f.locator(`input[name=q${i}][value="${v}"]`).check();await f.locator('#answer-5').fill('28.8');await f.locator('#answer-6').fill('28.8');await f.locator('#grade').click();assert.equal(await f.locator('#score').innerText(),'10 / 10 correct');await go(4);f=await go(7);assert.equal(await f.locator('#score').innerText(),'10 / 10 correct');await f.locator('#practice-outgoing').click();await f.locator('[data-valve-number="5"]').click();await f.locator('#check-valve-practice').click();assert.match(await f.locator('#valve-practice-feedback').innerText(),/Correct/);await f.locator('#reset-exercises').click();assert.equal(await f.locator('#score').innerText(),'');
  });
  await check('All 29 recordings load and browser-decoded signal hashes match source data',async()=>{
   const f=await go(6),manifest=JSON.parse(fs.readFileSync(path.join(root,'docs/data/manifest.json'),'utf8'));
   for(const entry of manifest.cases){await f.locator('#case-select').selectOption(entry.id);await f.locator('#load-status').waitFor({state:'hidden'});assert.ok((await f.locator('#primary-name').innerText()).startsWith(entry.id+' ·'));
    const raw=fs.readFileSync(path.join(root,'docs',entry.file),'utf8'),p=JSON.parse(raw.slice('window.registerCase('.length,-2)),bytes=zlib.inflateSync(Buffer.from(p.data,'base64')),expected={};
    p.fields.forEach((field,j)=>{const out=Buffer.alloc(p.samples*4);let previous=0;for(let i=0;i<p.samples;i++){let word=0;for(let b=0;b<4;b++)word|=bytes[j*4*p.samples+b*p.samples+i]<<(8*b);previous=(previous^word)>>>0;out.writeUInt32LE(previous,i*4);}expected[field]=crypto.createHash('sha256').update(out).digest('hex');});
    const actual=await page.evaluate(async id=>{const d=await HVDC_SINGLE_FILE.loadCase(id),hashes={};for(const [field,array] of Object.entries(d.signals)){const hash=await crypto.subtle.digest('SHA-256',array.buffer);hashes[field]=Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');}return hashes;},entry.id);
    assert.deepEqual(actual,expected,entry.id);
   }
  });
  await check('Recorded circuit state agrees with full-precision native CSV',async()=>{
   const f=await go(1),event=JSON.parse(fs.readFileSync(path.join(root,'results/validated_samples/CF-00_event.json')));await f.locator('#event-select').selectOption(event.event_id);await f.locator('#time').fill('6000');const t=Number((await f.locator('#time-value').innerText()).split(' ')[0]);const rows=fs.readFileSync(path.join(root,'results/validated_samples/CF-00_event.csv'),'utf8').trim().split(/\r?\n/).map(x=>x.split(',')),header=rows.shift(),sample=rows.find(r=>Math.abs(Number(r[0])-t)<1e-7);assert.ok(sample);const v=k=>Number(sample[header.indexOf(k)]),threshold=Math.max(1,.001*Math.abs(v('Idc_meas')));for(let k=1;k<=6;k++)assert.equal(/\bON\b/.test(await f.locator(`[data-valve-number="${k}"]`).innerText()),v('IT'+k)>threshold);
  });
  await check('PNG export, licenses and keyboard dialog behavior work offline',async()=>{
   const f=await go(3);const downloadPromise=page.waitForEvent('download');await f.locator('#export-plot').click();const download=await downloadPromise;assert.ok(fs.statSync(await download.path()).size>1000);
   await f.locator('#enlarge').click();await f.locator('#diagram-dialog').press('Escape');assert.equal(await f.locator('#diagram-dialog').isVisible(),false);
   await page.locator('#notices-open').click();assert.match(await page.locator('#notices-content').innerText(),/Permission is hereby granted/);await page.locator('#notices-close').click();
  });
  await check('Direct module hash and desktop visual preview',async()=>{await page.goto(url+'#3',{timeout:60000});const f=await frame('3');assert.match(await f.locator('#primary-name').innerText(),/CF-02/);assert.match(await f.locator('#reference-name').innerText(),/CF-00/);await page.screenshot({path:path.join(root,'.local/single-file-desktop.png')});});
  assert.deepEqual(blocked,[]);assert.deepEqual(errors,[]);results.push('No external requests, missing resources, JavaScript or CSP errors');
 }finally{
  fs.mkdirSync(path.join(root,'reports'),{recursive:true});fs.writeFileSync(path.join(root,'reports/single_file_browser_tests.json'),JSON.stringify({completed_at:new Date().toISOString(),mode:'Isolated single HTML, file://, network disabled',artifact_sha256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),passed:results,blocked_requests:blocked,errors},null,2));await browser.close();
  // Retain the isolated copy for reproducibility; it contains only the delivered HTML.
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
