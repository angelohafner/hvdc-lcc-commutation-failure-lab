const {chromium}=require('../.local/web/node_modules/playwright');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
process.chdir(path.resolve(__dirname,'..'));
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});
 await page.goto(pathToFileURL(path.resolve('docs/index.html')).href);await page.locator('#load-status').waitFor({state:'hidden'});
 await page.screenshot({path:'docs/assets/images/learning_hub.png'});
 await page.goto(pathToFileURL(path.resolve('docs/modules/03_normal_vs_failed_commutation.html')).href);await page.locator('#load-status').waitFor({state:'hidden'});
 await page.locator('#plot-columns').screenshot({path:'docs/assets/images/interactive_comparison.png'});
 await page.goto(pathToFileURL(path.resolve('docs/technical_report.html')).href);await page.locator('.katex').first().waitFor();await page.evaluate(()=>document.fonts.ready);
 await page.pdf({path:'reports/HVDC_LCC_Technical_Report.pdf',format:'A4',printBackground:true,margin:{top:'18mm',bottom:'18mm',left:'15mm',right:'15mm'},displayHeaderFooter:true,headerTemplate:'<span></span>',footerTemplate:'<div style="font-size:8px;color:#526d7e;width:100%;text-align:center">HVDC Commutation Failure Lab · <span class="pageNumber"></span> / <span class="totalPages"></span></div>'});
 await browser.close();console.log('Saved report PDF and website previews');
})().catch(e=>{console.error(e);process.exitCode=1;});
