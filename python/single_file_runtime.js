/* Offline packaging/navigation only. Native waveforms and teaching engines are unchanged. */
'use strict';
(()=>{
 const node=document.getElementById('single-file-bundle');
 const bundle=JSON.parse(node.textContent);node.remove();
 const routes=[...Array(8)].map((_,i)=>String(i)).concat('report');
 const selector=document.getElementById('module-switch'),stage=document.getElementById('stage');
 const status=document.getElementById('bundle-status'),frames=new Map(),cache=new Map(),pending=new Map();
 let active=null;
 for(const id of routes){const option=document.createElement('option');option.value=id;option.textContent=(id==='report'?'Report':id.padStart(2,'0'))+' · '+bundle.pages[id].title.replace(' | HVDC Lab','').replace('Technical report | HVDC Commutation Failure Lab','Technical report');selector.append(option);}
 async function loadCase(id){
  if(cache.has(id))return cache.get(id);
  if(pending.has(id))return pending.get(id);
  const source=bundle.recordings[id];if(!source)throw Error('Embedded recording is unavailable: '+id);
  const promise=(async()=>{
   const encoded=Uint8Array.from(atob(source.data),c=>c.charCodeAt(0));
   const stream=new Blob([encoded]).stream().pipeThrough(new DecompressionStream('deflate'));
   const bytes=await new Response(stream).arrayBuffer();
   if(bytes.byteLength!==source.samples*source.fields.length*4)throw Error('Embedded dataset size mismatch: '+id);
   const matrix=new DataView(bytes),signals={};
   source.fields.forEach((key,j)=>{const a=new Float32Array(source.samples),scratch=new DataView(new ArrayBuffer(4));let previous=0;
    for(let i=0;i<a.length;i++){
     if(source.data_layout==='xor-byteplanes-v1'){const start=j*4*a.length;let word=0;for(let b=0;b<4;b++)word|=matrix.getUint8(start+b*a.length+i)<<(8*b);previous=(previous^word)>>>0;scratch.setUint32(0,previous,true);a[i]=scratch.getFloat32(0,true);}
     else a[i]=matrix.getFloat32((i*source.fields.length+j)*4,true);
    }signals[key]=a;
   });
   const {data,...metadata}=source;const result={...metadata,signals};cache.set(id,result);return result;
  })();
  pending.set(id,promise);try{return await promise;}finally{pending.delete(id);}
 }
 function navigate(id){if(!routes.includes(id))return;if(location.hash==='#'+id)show(id);else location.hash=id;}
 const pageRoutes=Object.fromEntries(routes.map(id=>[bundle.pages[id].file,id]));
 const bridge=`<script>
 document.addEventListener('click',event=>{
  const a=event.target.closest('a[href]');if(!a)return;const href=a.getAttribute('href');
  if(href.startsWith('#')){event.preventDefault();const target=document.getElementById(decodeURIComponent(href.slice(1)));if(target){const had=target.hasAttribute('tabindex');if(!had)target.setAttribute('tabindex','-1');target.focus({preventScroll:true});target.scrollIntoView();if(!had)target.addEventListener('blur',()=>target.removeAttribute('tabindex'),{once:true});}return;}
  if(/^https?:/i.test(href)){a.target='_blank';a.rel='noopener noreferrer';return;}
  const parts=href.split('#'),name=parts[0].split('/').pop();
  const route=parent.HVDC_SINGLE_FILE.pageRoutes[name];
  if(route!==undefined){event.preventDefault();parent.HVDC_SINGLE_FILE.navigate(route);}
 });
 document.addEventListener('visibilitychange',()=>{if(document.hidden&&typeof pause==='function')pause();});
 </scr`+`ipt>`;
 function documentFor(id){
  let html=bundle.pages[id].html;
  html=html.replace(/<style data-offline-resource="([^"]+)"><\/style>/g,(_,key)=>'<style>'+bundle.resources[key]+'</style>');
  html=html.replace(/<script data-offline-resource="([^"]+)"><\/script>/g,(_,key)=>'<script>'+bundle.resources[key].replace(/<\/script/gi,'<\\/script')+'</scr'+'ipt>');
  return html.replace('</body>',bridge+'</body>');
 }
 function show(id){
  if(active===id)return;
  if(active!==null){const old=frames.get(active);if(old?.contentWindow?.pause)old.contentWindow.pause();if(old)old.hidden=true;}
  active=id;selector.value=id;const index=routes.indexOf(id);
  document.getElementById('module-previous').disabled=index===0;document.getElementById('module-next').disabled=index===routes.length-1;
  document.title=bundle.pages[id].title+' · Single-file virtual laboratory';
  let frame=frames.get(id);
  if(!frame){
   status.hidden=false;frame=document.createElement('iframe');frame.id='module-frame-'+id;frame.dataset.route=id;frame.title=bundle.pages[id].title;frames.set(id,frame);
   frame.addEventListener('load',()=>{if(active===id)status.hidden=true;});frame.srcdoc=documentFor(id);stage.append(frame);
  }else{frame.hidden=false;status.hidden=true;frame.contentWindow.dispatchEvent(new Event('resize'));}
 }
 window.HVDC_SINGLE_FILE=Object.freeze({loadCase,navigate,pageRoutes});
 selector.addEventListener('change',()=>navigate(selector.value));
 document.getElementById('module-previous').onclick=()=>navigate(routes[routes.indexOf(active)-1]);
 document.getElementById('module-next').onclick=()=>navigate(routes[routes.indexOf(active)+1]);
 addEventListener('hashchange',()=>show(routes.includes(location.hash.slice(1))?location.hash.slice(1):'0'));
 document.addEventListener('visibilitychange',()=>{if(document.hidden){const w=frames.get(active)?.contentWindow;if(w?.pause)w.pause();}});
 const notices=document.getElementById('notices'),content=document.getElementById('notices-content');
 for(const [title,text] of Object.entries({...bundle.notices,'Data integrity':JSON.stringify({source:bundle.manifest.source,recordings:bundle.manifest.cases.map(c=>({id:c.id,sha256:c.sha256})),scope:bundle.scope},null,2)})){
  const h=document.createElement('h2'),pre=document.createElement('pre');h.textContent=title;pre.textContent=text;content.append(h,pre);
 }
 document.getElementById('notices-open').onclick=()=>{const w=frames.get(active)?.contentWindow;if(w?.pause)w.pause();notices.showModal();};
 document.getElementById('notices-close').onclick=()=>notices.close();
 // Print the active document in the top-level flow: a viewport-sized iframe clips it.
 const printRules=document.createElement('style');
 printRules.textContent='#print-document{display:none}@media print{html,body{height:auto!important;display:block!important}.shell,.stage,#notices{display:none!important}#print-document{display:block!important}.report-figure{width:100%;height:auto}}';document.head.append(printRules);
 let printState=null;
 function endPrint(){
  document.getElementById('print-document')?.remove();
  if(printState){document.body.className=printState.className;if(printState.page===undefined)delete document.body.dataset.page;else document.body.dataset.page=printState.page;printState=null;}
 }
 addEventListener('beforeprint',()=>{
  endPrint();const frame=frames.get(active),doc=frame?.contentDocument;if(!doc?.body)return;
  if(frame.contentWindow.pause)frame.contentWindow.pause();
  printState={className:document.body.className,page:document.body.dataset.page};
  document.body.className=doc.body.className;if(doc.body.dataset.page)document.body.dataset.page=doc.body.dataset.page;
  const section=document.createElement('div');section.id='print-document';
  const style=document.createElement('style');style.textContent=[...doc.head.querySelectorAll('style')].map(s=>s.textContent).join('\n')+'\n'+printRules.textContent;section.append(style);
  const clone=doc.body.cloneNode(true),canvases=[...doc.querySelectorAll('canvas')];
  clone.querySelectorAll('canvas').forEach((canvas,i)=>{const image=document.createElement('img');image.src=canvases[i].toDataURL('image/png');image.alt=canvas.getAttribute('aria-label')||'Recorded waveform';image.style.width='100%';canvas.replaceWith(image);});
  clone.querySelectorAll('script,template,dialog').forEach(node=>node.remove());
  section.append(...clone.childNodes);document.body.append(section);
 });
 addEventListener('afterprint',endPrint);
 const initial=routes.includes(location.hash.slice(1))?location.hash.slice(1):'0';if(location.hash!=='#'+initial)history.replaceState(null,'','#'+initial);show(initial);
})();
