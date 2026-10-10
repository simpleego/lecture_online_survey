let authorization = "";
let page = 1;
let activeFilters = new URLSearchParams();
const $ = id => document.getElementById(id);
const labels = {
  student_name: "이름", team_name: "팀", created_at: "제출일", id: "접수번호",
  understanding_level: "수업 이해도", understanding_good: "잘 이해되는 부분", understanding_difficult: "어려운 부분", understanding_areas: "이해 분야",
  practice_level: "실습 수준", practice_status: "실습 단계", practice_comment: "실습 의견",
  hardest_points: "학습 중 어려운 점", hardest_comment: "어려움 상세 의견",
  review_frequency: "복습 빈도", ai_learning_usage: "AI 학습 활용", improvement_method: "보완 방법",
  project_role: "현재 역할", desired_role: "희망 역할", collaboration_difficulty: "협업 어려움", project_strength: "프로젝트 강점", project_burden: "프로젝트 부담",
  ai_tool_level: "AI 도구 활용", ai_tool_usage: "AI 활용 목적", code_understanding: "생성 코드 이해", ai_tool_comment: "AI 활용 의견",
  desired_job: "희망 직무", career_fields: "관심 분야", course_career_fit: "진로 적합도", career_comment: "진로 고민",
  class_speed: "수업 속도", need_more_explanation: "추가 설명 요청", practice_amount: "실습량", instructor_support: "강사 지원 요청"
};
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function message(text, type = "error") { $("message").textContent = text; $("message").className = `message ${type}`; }
function logout() {
  authorization = "";
  managedQuestions=[]; resetEditor();
  $("password").value = "";
  $("dashboard").classList.add("hidden");
  $("loginPanel").classList.remove("hidden");
  ["statistics", "responseRows", "detail", "evaluations", "questionRows", "questionAnalysis"].forEach(id => $(id).replaceChildren());
  $("detailPanel").classList.add("hidden");
}
async function api(url, method='GET', payload) {
  const requestAuthorization=authorization;
  const response = await fetch(url, { method, headers: { Authorization: authorization, 'Content-Type':'application/json' }, cache: 'no-store', body:payload===undefined?undefined:JSON.stringify(payload) });
  if(requestAuthorization!==authorization)throw new Error('로그인 상태가 변경되었습니다.');
  if (!response.ok) {
    const error = await response.json();
    if (response.status === 401) logout();
    throw new Error(typeof error.detail === "string" ? error.detail : "입력 내용을 확인해 주세요.");
  }
  return response.json();
}
function date(value) { return value ? value.replace("T", " ") : "—"; }
function flags(parent, entries) {
  if (!entries.length) { parent.append(el("p", "현재 기준에 해당하는 상담 확인 항목이 없습니다.")); return; }
  const list = el("ul", undefined, "flags");
  entries.forEach(entry => list.append(el("li", entry)));
  parent.append(list);
}
function bars(parent, title, values, percent = false, kind='column', multiple=false) {
  SurveyCharts.render(parent,title,values,percent,kind,multiple);
}
const scoreAxisLabels = {'1':'1 매우 낮음','2':'2 낮음','3':'3 보통','4':'4 높음','5':'5 매우 높음'};
function scoreDistribution(values) {
  return values.map(value=>({...value,label:scoreAxisLabels[value.label] || value.label}));
}
function renderStats(data) {
  const root = $("statistics"); root.replaceChildren();
  const metrics = el("div", undefined, "metric-grid");
  [["설문 응답 수", data.response_count], ["상담 확인 응답 수", data.flagged_count],
    ...Object.values(data.scores).map(s => [`${s.label} 평균`, s.average === null ? "—" : `${s.average} / 5`])].forEach(([title, value]) => {
    const metric = el("div", title, "metric"); metric.append(el("strong", value)); metrics.append(metric);
  });
  root.append(metrics);
  Object.values(data.scores).forEach(s => bars(root, `${s.label} 분포 (${s.count}건 · 미응답 ${s.missing || 0}건)`, scoreDistribution(s.distribution)));
  bars(root, "복습 빈도", data.review_frequency, true, "pie");
  bars(root, "학습 어려움 순위", data.hardest_points, true, "pie", true);
  bars(root, "관심 분야", data.career_fields, true, "pie", true);
  root.append(el("h3", "팀별 비교 · 응답 수 기준"));
  const table = el("table"); const head = el("tr");
  ["팀", "응답 수", "이해도", "실습", "AI 활용", "진로 적합"].forEach(text => head.append(el("th", text))); table.append(head);
  data.teams.forEach(team => { const row = el("tr"); [team.team_name, team.response_count, ...Object.values(team.scores).map(s => s.average)].forEach(value => row.append(el("td", value ?? "—"))); table.append(row); });
  const scroll = el("div", undefined, "table-scroll"); scroll.append(table); root.append(scroll);
  const questionRoot = $('questionAnalysis'); questionRoot.replaceChildren();
  const questionData = (data.questions || []).filter(q=>q.answered || !managedQuestions.some(m=>m.id===q.question_id && m.legacy_key));
  if(!questionData.length)questionRoot.append(el('p','새 설문항목의 응답이 아직 없습니다.'));
  questionData.forEach(q=>{
    const section=el('details');section.append(el('summary',`${q.topic} · 응답 ${q.answered}건`));
    section.append(el('p',`미응답 ${q.missing}건 · 작성 당시 구성 기준`));
    const binding=managedQuestions.find(m=>m.id===q.question_id)?.legacy_key;
    const isScore=q.kind==='single' && ['understanding_level','practice_level','ai_tool_level','course_career_fit'].includes(binding);
    if(q.kind!=='text')bars(section,'응답 분포',isScore?scoreDistribution(q.distribution):q.distribution,true,'column',q.kind==='multiple');
    q.comments.forEach(c=>{const box=el('div',undefined,'comment');box.append(el('p',`#${c.survey_id} ${c.student_name}`),el('p',c.comment,'answer'));section.append(box);});
    questionRoot.append(section);
  });
  const evaluation = $("evaluations"); evaluation.replaceChildren();
  [["9. 학습환경", data.learn_env], ["10. 건물 인프라 및 편의 지원", data.facillities]].forEach(([title, items]) => {
    evaluation.append(el("h3", title));
    items.forEach(item => {
      const section = el("details"); section.append(el("summary", `${item.item_name} · 평균 ${item.average ?? "—"} / 5 · 점수 응답 ${item.rated}건`));
      section.append(el("p", `응답 ${item.answered}건 / 미응답 ${item.missing}건 / 점수 제외 ${item.excluded}건`));
      bars(section, "응답 분포", item.distribution, true);
      section.append(el("h4", `개별 의견 ${item.comments.length}건`));
      item.comments.forEach(c => { const box = el("div", undefined, "comment"); box.append(el("p", `#${c.survey_id} ${c.student_name} · ${c.satisfaction}`), el("p", c.comment, "answer")); section.append(box); });
      evaluation.append(section);
    });
  });
}
async function showDetail(id) {
  try {
    const data = await api(`/api/admin/surveys/${id}`);
    const root = $("detail"); root.replaceChildren();
    root.append(el("h3", `${data.response.student_name} · ${data.response.team_name || "팀 미선택"} · #${id}`));
    const summary = data.summary;
    root.append(el("p", `${Object.entries(summary.scores).map(([k,v]) => `${k} ${v===null?'미응답':`${v}점`}`).join(" / ")} · 복습: ${summary.review_frequency || '미응답'}`));
    root.append(el("p", `실습 단계: ${summary.practice_status}`), el("p", `어려운 점: ${summary.hardest_points.join(", ") || "선택 없음"}`), el("p", `강점: ${summary.strength || "작성 없음"}`, "answer"), el("p", `지원 요청: ${summary.support_request || "작성 없음"}`, "answer"));
    root.append(el("h3", "상담 확인 항목")); flags(root, summary.flags);
    const full = el("details"); full.append(el("summary", "전체 응답 보기"));
    Object.entries(labels).forEach(([key, label]) => { full.append(el("h4", label), el("p", key === "created_at" ? date(data.response[key]) : (data.response[key] ?? "작성 없음") || "작성 없음", "answer")); });
    [["9. 학습환경", "learn_env_answers", data.learn_env_items], ["10. 건물 인프라", "facillities_answers", data.facillities_items]].forEach(([title, key, items]) => {
      const names = new Map(items.map(item => [item.id, item.item_name]));
      full.append(el("h3", title));
      if (!data.response[key].length) full.append(el("p", "응답 없음"));
      data.response[key].forEach(answer => full.append(el("h4", names.get(answer.item_id) || `이전 항목 #${answer.item_id}`), el("p", answer.satisfaction), el("p", answer.comment || "의견 없음", "answer")));
    });
    if(data.response.question_answers){
      const saved=el('details');saved.open=true;saved.append(el('summary','작성 당시 설문 · 전체 답변'));
      data.response.question_answers.forEach(a=>{saved.append(el('h4',a.question.topic),el('p',Array.isArray(a.value)?a.value.join(', ')||'미응답':a.value||'미응답','answer'));if(a.comment)saved.append(el('p',a.comment,'answer'));});
      root.append(saved);
    } else root.append(full);
    $('detailPanel').classList.remove("hidden"); $("detailPanel").scrollIntoView({ behavior: "smooth" });
  } catch (error) { message(error.message); }
}
async function loadList() {
  const query = new URLSearchParams(activeFilters); query.set("page", page);
  const data = await api(`/api/admin/surveys?${query}`);
  const root = $("responseRows"); root.replaceChildren();
  data.items.forEach(item => {
    const row = el("tr");
    [item.id, item.student_name, item.team_name || "미선택", date(item.created_at), `${item.summary.scores['수업 이해도'] ?? '—'} / ${item.summary.scores['실습 수준'] ?? '—'}`, `${item.summary.flags.length}개`].forEach(value => row.append(el("td", value)));
    const cell = el("td"); const button = el("button", "상세 보기"); button.type = "button"; button.addEventListener("click", () => showDetail(item.id)); cell.append(button); row.append(cell); root.append(row);
  });
  if (!data.items.length) { const row = el("tr"); const cell = el("td", "조건에 해당하는 응답이 없습니다."); cell.colSpan = 7; row.append(cell); root.append(row); }
  $("pageInfo").textContent = `${page} / ${Math.max(1, Math.ceil(data.total / data.page_size))} 페이지 · ${data.total}건`;
  $("previous").disabled = page <= 1; $("next").disabled = page * data.page_size >= data.total;
}
async function refresh() {
  $("detailPanel").classList.add("hidden"); $("message").className = "message hidden";
  try { const [stats] = await Promise.all([api(`/api/admin/statistics?${activeFilters}`), loadList()]); renderStats(stats); }
  catch (error) { message(error.message); }
}
$("loginForm").addEventListener("submit", async event => {
  event.preventDefault();
  authorization = `Basic ${btoa(unescape(encodeURIComponent(`${$("username").value}:${$("password").value}`)))}`;
  try {
    await api("/api/admin/session"); $("password").value = "";
    const teams = await api("/api/teams"); $("teamFilter").replaceChildren(new Option("전체 팀", "")); teams.forEach(t => $("teamFilter").add(new Option(t.team_name, t.team_name)));
    $("loginPanel").classList.add("hidden"); $("dashboard").classList.remove("hidden"); page = 1; activeFilters = new URLSearchParams(); $("nameFilter").value = "";
    await loadQuestions();
    selectTab("analysis");
    await refresh();
  } catch (error) { logout(); message(error.message); }
});
$("filterForm").addEventListener("submit", event => { event.preventDefault(); page = 1; activeFilters = new URLSearchParams({ name: $("nameFilter").value.trim(), team: $("teamFilter").value }); refresh(); });
$("previous").addEventListener("click", async () => { page--; try { await loadList(); } catch(error) { message(error.message); } });
$("next").addEventListener("click", async () => { page++; try { await loadList(); } catch(error) { message(error.message); } });
$("logout").addEventListener("click", () => { logout(); message("로그아웃했습니다.", "success"); });
$("closeDetail").addEventListener("click", () => $("detailPanel").classList.add("hidden"));

let managedQuestions=[];
let editingQuestion=null;
const kindLabels={text:'기술형',single:'단일선택',multiple:'다중선택'};
function selectTab(tab) {
  for(const name of ['management','analysis']) {
    const active=name===tab;
    $(`${name}Tab`).setAttribute('aria-selected',String(active));
    $(`${name}Tab`).tabIndex=active?0:-1;
    $(`${name}Panel`).classList.toggle('hidden',!active);
  }
  if(tab==='analysis' && typeof SurveyCharts !== 'undefined')requestAnimationFrame(()=>SurveyCharts.redraw());
}
for(const tab of ['management','analysis']) {
  $(`${tab}Tab`).addEventListener('click',()=>selectTab(tab));
  $(`${tab}Tab`).addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?'management':event.key==='End'?'analysis':tab==='management'?'analysis':'management';selectTab(next);$(`${next}Tab`).focus();}});
}
function optionsVisibility() {
  const text=$('questionKind').value==='text';
  $('optionsField').classList.toggle('hidden',text);
  $('questionOptions').required=!text;
}
function resetEditor() {
  editingQuestion=null;$('questionForm').reset();$('editorTitle').textContent='새 설문항목 추가';
  $('saveQuestion').textContent='추가하기';$('deleteQuestion').classList.add('hidden');$('bindingHint').textContent='';
  optionsVisibility();document.querySelectorAll('#questionRows tr').forEach(n=>n.classList.remove('selected'));
}
function editQuestion(q) {
  editingQuestion=q;$('editorTitle').textContent='설문항목 수정';$('saveQuestion').textContent='수정 저장';
  $('questionSection').value=q.section;$('questionTopic').value=q.topic;$('questionKind').value=q.kind;
  $('questionOptions').value=q.options.join('\n');$('questionOrder').value=q.sort_order;
  $('questionRequired').checked=q.required;$('questionComment').checked=q.allow_comment;
  $('deleteQuestion').classList.remove('hidden');
  $('bindingHint').textContent=q.legacy_key?'기존 설문항목입니다. 구성 변경은 앞으로 작성하는 설문에 적용됩니다. 기존 답변은 작성 당시 내용으로 유지됩니다.':'';
  optionsVisibility();document.querySelectorAll('#questionRows tr').forEach(n=>n.classList.toggle('selected',Number(n.dataset.id)===q.id));
  $('questionEditor').scrollIntoView({behavior:'smooth',block:'start'});$('questionTopic').focus();
}
async function loadQuestions() {
  const data=await api('/api/admin/questions');managedQuestions=data.questions;
  $('questionCount').textContent=`총 ${managedQuestions.length}개 항목`;
  const root=$('questionRows');root.replaceChildren();
  managedQuestions.forEach(q=>{const row=el('tr');row.dataset.id=q.id;
    [q.sort_order,q.section,q.topic,kindLabels[q.kind],q.required?'필수':'선택'].forEach(t=>row.append(el('td',t)));
    const cell=el('td'),edit=el('button','선택 / 수정'),remove=el('button','삭제','danger');edit.type=remove.type='button';
    edit.addEventListener('click',()=>editQuestion(q));remove.addEventListener('click',()=>removeQuestion(q));
    const actions=el('div',undefined,'actions');actions.append(edit,remove);cell.append(actions);row.append(cell);root.append(row);
  });
  if(!managedQuestions.length){const row=el('tr'),cell=el('td','등록된 설문항목이 없습니다. 새 항목을 추가해 주세요.');cell.colSpan=6;row.append(cell);root.append(row);}
}
async function removeQuestion(q) {
  if(!confirm(`“${q.topic}” 항목을 삭제할까요?\n새 설문에서는 제외되며, 기존 응답은 보존됩니다.`))return;
  try{await api(`/api/admin/questions/${q.id}?revision=${q.revision}`,'DELETE');resetEditor();await loadQuestions();await refresh();message('설문항목을 삭제했습니다.','success');}
  catch(e){message(e.message);}
}
$('questionKind').addEventListener('change',optionsVisibility);
$('newQuestion').addEventListener('click',()=>{resetEditor();$('questionEditor').scrollIntoView({behavior:'smooth'});$('questionTopic').focus();});
$('cancelQuestion').addEventListener('click',resetEditor);
$('reloadQuestions').addEventListener('click',async()=>{try{resetEditor();await loadQuestions();message('목록을 새로 불러왔습니다.','success');}catch(e){message(e.message);}});
$('deleteQuestion').addEventListener('click',()=>{if(editingQuestion)removeQuestion(editingQuestion);});
$('questionForm').addEventListener('submit',async event=>{
  event.preventDefault();const kind=$('questionKind').value;
  const options=kind==='text'?[]:$('questionOptions').value.split('\n').map(v=>v.trim()).filter(Boolean);
  if(kind!=='text'&&(options.length<2||new Set(options).size!==options.length)){message('서로 다른 선택지를 2개 이상 입력해 주세요.');return;}
  const payload={topic:$('questionTopic').value.trim(),section:$('questionSection').value.trim(),kind,options,
    required:$('questionRequired').checked,allow_comment:$('questionComment').checked,sort_order:Number($('questionOrder').value)};
  if(editingQuestion)payload.revision=editingQuestion.revision;
  $('saveQuestion').disabled=true;
  try{await api(editingQuestion?`/api/admin/questions/${editingQuestion.id}`:'/api/admin/questions',editingQuestion?'PUT':'POST',payload);
    resetEditor();await loadQuestions();await refresh();message('설문항목을 저장했습니다. 설문 작성 화면에 적용됩니다.','success');}
  catch(e){message(e.message);}finally{$('saveQuestion').disabled=false;}
});
optionsVisibility();
