const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const root = path.resolve(__dirname,'../..');
const cfg = Object.fromEntries(fs.readFileSync(path.join(root,'.env'),'utf8').split(/\r?\n/).filter(l=>l.includes('=')).map(l=>{const i=l.indexOf('=');return [l.slice(0,i),l.slice(i+1)];}));
const base='http://127.0.0.1:8003';
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 const errors=[];const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/admin');
 await page.locator('#username').fill(cfg.ADMIN_USER);await page.locator('#password').fill(cfg.ADMIN_PASSWORD);
 await page.locator('#loginForm button').click();await page.locator('#dashboard').waitFor({state:'visible'});
 await page.locator('#responseRows tr').first().waitFor();
 assert((await page.locator('#pageInfo').textContent()).includes('61건'));
 await page.waitForFunction(()=>document.querySelectorAll('.google-chart[data-drawn="true"]').length>=7,{},{timeout:30000});
 const drawn=await page.locator('.google-chart[data-drawn="true"]').count();assert(drawn>=7);
 await page.screenshot({path:path.join(root,'admin-v4-preview.png'),fullPage:true});
 await page.locator('#next').click();await page.waitForFunction(()=>document.querySelector('#pageInfo').textContent.startsWith('2 /'));
 await page.locator('#responseRows button').first().click();await page.locator('#detailPanel').waitFor({state:'visible'});
 await page.locator('#managementTab').click();await page.locator('#managementPanel').waitFor({state:'visible'});
 assert.equal(await page.locator('#questionRows tr').count(),36);
 await page.screenshot({path:path.join(root,'management-v4-preview.png'),fullPage:true});
 const real=await page.request.get(base+'/api/v4/questions');let form=await real.json();let questions=structuredClone(form.questions);let next=10000;
 // Exercise UI saves/deletes against mocked transport: production DB remains at 61 responses.
 await page.route(/\/api\/admin\/questions(?:\/[^?]*)?(?:\?.*)?$/,async route=>{
   const req=route.request(),url=new URL(req.url()),id=Number(url.pathname.split('/').pop());
   if(req.method()==='GET')return route.fulfill({json:{revision:form.revision,questions}});
   if(req.method()==='POST'){const data=req.postDataJSON();questions.push({...data,id:next++,legacy_key:null,revision:1,deleted:0});return route.fulfill({status:201,json:{id:next-1}});}
   if(req.method()==='PUT'){const data=req.postDataJSON();questions=questions.map(q=>q.id===id?{...q,...data,revision:q.revision+1}:q);return route.fulfill({json:{status:'updated'}});}
   if(req.method()==='DELETE'){questions=questions.filter(q=>q.id!==id);return route.fulfill({json:{status:'deleted'}});}
 });
 for(const kind of ['text','single','multiple']){
   await page.locator('#newQuestion').click();await page.locator('#questionTopic').fill('화면검증 '+kind);
   await page.locator('#questionKind').selectOption(kind);
   if(kind!=='text')await page.locator('#questionOptions').fill('기초\n심화');
   await page.locator('#saveQuestion').click();await page.locator('#questionRows tr').filter({hasText:'화면검증 '+kind}).waitFor();
 }
 assert.equal(questions.length,39);
 const row=page.locator('#questionRows tr').filter({hasText:'화면검증 single'});
 await row.getByRole('button',{name:'선택 / 수정'}).click();await page.locator('#questionTopic').fill('변경된 검증 주제');await page.locator('#saveQuestion').click();
 await page.locator('#questionRows tr').filter({hasText:'변경된 검증 주제'}).waitFor();
 page.once('dialog',d=>d.accept());await page.locator('#questionRows tr').filter({hasText:'변경된 검증 주제'}).getByRole('button',{name:'삭제',exact:true}).click();
 await page.waitForFunction(()=>!document.querySelector('#questionRows').textContent.includes('변경된 검증 주제'));assert.equal(questions.length,38);
 const survey=await context.newPage();survey.on('pageerror',e=>errors.push(e.message));
 await survey.route('**/api/v4/questions',route=>route.fulfill({json:{revision:form.revision,questions}}));
 let submission=null;
 await survey.route('**/api/v4/surveys',route=>{submission=route.request().postDataJSON();return route.fulfill({status:201,json:{id:'v4-검증'}});});
 await survey.goto(base+'/');await survey.locator('#submitBtn').waitFor({state:'visible'});await survey.waitForFunction(()=>!document.querySelector('#submitBtn').disabled);
 assert.equal(await survey.locator('#dynamicQuestions fieldset').count(),38);
 assert.equal(await survey.locator('#dynamicQuestions select').evaluateAll(nodes=>nodes.filter(n=>n.value!=='').length),0);
 await survey.locator('#student_name').fill('화면검증');
 for(const select of await survey.locator('#dynamicQuestions select').all())await select.selectOption({index:1});
 for(const box of await survey.locator('#dynamicQuestions fieldset').all()){
   if((await box.locator('input[type=checkbox]').count())>0)await box.locator('input[type=checkbox]').first().check();
   for(const textarea of await box.locator('textarea').all())await textarea.fill('가상 화면 검증 답변');
 }
 await survey.locator('#submitBtn').click();await survey.locator('#message.success').waitFor();
 assert(submission && submission.answers.length===38);assert.equal(submission.student_name,'화면검증');
 const typed=questions.find(q=>q.topic==='화면검증 text');assert.equal(submission.answers.find(a=>a.question_id===typed.id).value,'가상 화면 검증 답변');
 const multi=questions.find(q=>q.topic==='화면검증 multiple');assert.deepEqual(submission.answers.find(a=>a.question_id===multi.id).value,['기초']);
 await page.setViewportSize({width:390,height:844});await page.locator('#analysisTab').click();await page.waitForTimeout(250);
 assert(await page.locator('#analysisPanel').isVisible());
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({chartsDrawn:drawn,baselineQuestions:36,uiCrud:'passed',dynamicForm:'passed',pageErrors:errors,savedProductionResponses:0}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
