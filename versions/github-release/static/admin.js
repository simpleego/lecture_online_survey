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
  $("password").value = "";
  $("dashboard").classList.add("hidden");
  $("loginPanel").classList.remove("hidden");
  ["statistics", "responseRows", "detail", "evaluations"].forEach(id => $(id).replaceChildren());
  $("detailPanel").classList.add("hidden");
}
async function api(url) {
  const response = await fetch(url, { headers: { Authorization: authorization }, cache: "no-store" });
  if (!response.ok) {
    const error = await response.json();
    if (response.status === 401) logout();
    throw new Error(error.detail || "조회 중 오류가 발생했습니다.");
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
function bars(parent, title, values, percent = false) {
  parent.append(el("h3", title));
  if (!values.length) { parent.append(el("p", "응답 없음")); return; }
  const max = Math.max(1, ...values.map(v => v.count));
  values.forEach(value => {
    const row = el("div", undefined, "bar-row");
    const bar = el("progress"); bar.max = max; bar.value = value.count;
    row.append(el("span", value.label), bar, el("span", `${value.count}건${percent ? ` (${value.percent}%)` : ""}`));
    parent.append(row);
  });
}
function renderStats(data) {
  const root = $("statistics"); root.replaceChildren();
  const metrics = el("div", undefined, "metric-grid");
  [["설문 응답 수", data.response_count], ["상담 확인 응답 수", data.flagged_count],
    ...Object.values(data.scores).map(s => [`${s.label} 평균`, s.average === null ? "—" : `${s.average} / 5`])].forEach(([title, value]) => {
    const metric = el("div", title, "metric"); metric.append(el("strong", value)); metrics.append(metric);
  });
  root.append(metrics);
  Object.values(data.scores).forEach(s => bars(root, `${s.label} 분포 (${s.count}건)`, s.distribution));
  bars(root, "복습 빈도", data.review_frequency, true);
  bars(root, "학습 어려움 순위 · 비율은 전체 응답 대비, 복수 선택", data.hardest_points, true);
  bars(root, "관심 분야 · 비율은 전체 응답 대비, 복수 선택", data.career_fields, true);
  root.append(el("h3", "팀별 비교 · 응답 수 기준"));
  const table = el("table"); const head = el("tr");
  ["팀", "응답 수", "이해도", "실습", "AI 활용", "진로 적합"].forEach(text => head.append(el("th", text))); table.append(head);
  data.teams.forEach(team => { const row = el("tr"); [team.team_name, team.response_count, ...Object.values(team.scores).map(s => s.average)].forEach(value => row.append(el("td", value ?? "—"))); table.append(row); });
  const scroll = el("div", undefined, "table-scroll"); scroll.append(table); root.append(scroll);
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
    root.append(el("p", `${Object.entries(summary.scores).map(([k,v]) => `${k} ${v}점`).join(" / ")} · 복습: ${summary.review_frequency}`));
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
    root.append(full); $("detailPanel").classList.remove("hidden"); $("detailPanel").scrollIntoView({ behavior: "smooth" });
  } catch (error) { message(error.message); }
}
async function loadList() {
  const query = new URLSearchParams(activeFilters); query.set("page", page);
  const data = await api(`/api/admin/surveys?${query}`);
  const root = $("responseRows"); root.replaceChildren();
  data.items.forEach(item => {
    const row = el("tr");
    [item.id, item.student_name, item.team_name || "미선택", date(item.created_at), `${item.summary.scores['수업 이해도']} / ${item.summary.scores['실습 수준']}`, `${item.summary.flags.length}개`].forEach(value => row.append(el("td", value)));
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
    await refresh();
  } catch (error) { logout(); message(error.message); }
});
$("filterForm").addEventListener("submit", event => { event.preventDefault(); page = 1; activeFilters = new URLSearchParams({ name: $("nameFilter").value.trim(), team: $("teamFilter").value }); refresh(); });
$("previous").addEventListener("click", async () => { page--; try { await loadList(); } catch(error) { message(error.message); } });
$("next").addEventListener("click", async () => { page++; try { await loadList(); } catch(error) { message(error.message); } });
$("logout").addEventListener("click", () => { logout(); message("로그아웃했습니다.", "success"); });
$("closeDetail").addEventListener("click", () => $("detailPanel").classList.add("hidden"));
