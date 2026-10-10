const { chromium }=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'../..');
const cfg=Object.fromEntries(fs.readFileSync(path.join(root,'.env'),'utf8').split(/\r?\n/).filter(l=>l.includes('=')).map(l=>{const i=l.indexOf('=');return[l.slice(0,i),l.slice(i+1)];}));
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 let oldScriptUsed=false;
 const oldScript=fs.readFileSync(path.resolve(root,'../v3/static/admin.js'),'utf8');
 await page.route(/\/static\/admin\.js(?:\?.*)?$/,route=>{
   if(!new URL(route.request().url()).search){oldScriptUsed=true;return route.fulfill({contentType:'application/javascript',body:oldScript});}
   return route.continue();
 });
 // Google connectivity must never prevent switching between local menus.
 await page.route('https://www.gstatic.com/**',route=>route.abort());
 await page.goto('http://127.0.0.1:8003/admin');
 await page.locator('#username').fill(cfg.ADMIN_USER);await page.locator('#password').fill(cfg.ADMIN_PASSWORD);
 await page.locator('#loginForm button').click();await page.locator('#dashboard').waitFor({state:'visible'});
 await page.locator('#responseRows tr').first().waitFor();
 await page.locator('#managementTab').click();await page.waitForTimeout(150);
 const management=await page.locator('#managementPanel').isVisible();
 if(process.argv.includes('--reproduce')){
   assert(oldScriptUsed);assert(!management);console.log('Reproduced: stale v3 script leaves both tab buttons without handlers');
 }else{
   assert(!oldScriptUsed,'Unversioned script was loaded');assert(management);
   await page.locator('#analysisTab').click();assert(await page.locator('#analysisPanel').isVisible());
   await page.locator('#analysisTab').press('ArrowLeft');assert(await page.locator('#managementPanel').isVisible());
   assert.deepEqual(errors,[]);console.log('Passed: stale script bypassed, both tabs and keyboard navigation work with Google Charts offline');
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
