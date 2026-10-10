let currentForm = null;
const controls = new Map();
const $ = id => document.getElementById(id);
function node(tag, text) { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; return n; }
function showMessage(text,type='error') { $('message').textContent=text; $('message').className=`message ${type}`; $('message').scrollIntoView({behavior:'smooth',block:'center'}); }
async function get(path) { const r=await fetch(path,{cache:'no-store'}); if(!r.ok)throw new Error('설문 목록을 불러오지 못했습니다. 새로고침해 주세요.'); return r.json(); }
function renderQuestion(q,section) {
  const box=node('fieldset'); box.className='evaluation-item';
  box.append(node('legend',`${q.topic}${q.required?' *':''}`));
  const record={question:q,box,inputs:[]};
  if(q.kind==='text') {
    const input=node('textarea'); input.maxLength=5000; input.required=q.required; input.setAttribute('aria-label',q.topic); box.append(input); record.inputs.push(input);
  } else if(q.kind==='single') {
    const input=node('select'); input.required=q.required; input.setAttribute('aria-label',q.topic); input.add(new Option('선택하세요',''));
    q.options.forEach(option=>input.add(new Option(option,option))); box.append(input); record.inputs.push(input);
    if(q.legacy_key && ['understanding_level','practice_level','ai_tool_level','course_career_fit'].includes(q.legacy_key)) box.append(node('p','1 매우 낮음 · 2 낮음 · 3 보통 · 4 높음 · 5 매우 높음'));
  } else {
    const grid=node('div'); grid.className='check-grid';
    q.options.forEach(option=>{ const label=node('label'); const input=node('input'); input.type='checkbox'; input.value=option; label.append(input,document.createTextNode(` ${option}`)); grid.append(label); record.inputs.push(input); }); box.append(grid);
  }
  if(q.allow_comment) { const label=node('label','추가 의견 (선택)'); const comment=node('textarea'); comment.maxLength=5000; label.append(comment); box.append(label); record.comment=comment; }
  section.append(box); controls.set(q.id,record);
}
async function load() {
  try {
    const [form,teams]=await Promise.all([get('/api/v4/questions'),get('/api/teams')]);
    currentForm=form; $('team_name').replaceChildren(new Option('팀 미선택','')); teams.forEach(t=>$('team_name').add(new Option(t.team_name,t.team_name))); $('team_name').disabled=false;
    const root=$('dynamicQuestions'); root.replaceChildren(); controls.clear();
    let previousSection=null,section=null;
    form.questions.forEach(q=>{if(q.section!==previousSection){section=node('section');section.className='card';section.append(node('h2',q.section));root.append(section);previousSection=q.section;}renderQuestion(q,section);});
    if(!form.questions.length) root.append(node('p','현재 등록된 설문항목이 없습니다.'));
    $('submitBtn').disabled=false;
  } catch(e) {showMessage(e.message);}
}
$('surveyForm').addEventListener('submit',async event=>{
  event.preventDefault(); if(!currentForm || $('submitBtn').disabled)return;
  const answers=[];
  for(const [id,c] of controls) {
    const value=c.question.kind==='multiple'?c.inputs.filter(n=>n.checked).map(n=>n.value):c.inputs[0].value.trim()||null;
    if(c.question.required && Array.isArray(value) && !value.length){showMessage(`${c.question.topic}: 하나 이상 선택해 주세요.`);c.inputs[0]?.focus();return;}
    answers.push({question_id:id,value,comment:c.comment?.value.trim()||null});
  }
  if(!$('surveyForm').reportValidity())return;
  $('submitBtn').disabled=true; $('submitBtn').textContent='저장 중...';
  try {
    const r=await fetch('/api/v4/surveys',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({student_name:$('student_name').value.trim(),team_name:$('team_name').value||null,form_revision:currentForm.revision,answers})});
    const data=await r.json(); if(!r.ok)throw new Error(typeof data.detail==='string'?data.detail:'입력 내용을 확인해 주세요.');
    $('surveyForm').reset();showMessage(`설문이 저장되었습니다. 접수번호: ${data.id}`,'success');
  } catch(e){showMessage(e.message);} finally {$('submitBtn').disabled=false;$('submitBtn').textContent='설문 제출하기';}
});
load();
