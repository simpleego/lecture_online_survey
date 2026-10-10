const API_URL = "/api/surveys";

async function loadTeams() {
  const select = document.getElementById("team_name");
  try {
    const response = await fetch("/api/teams");
    if (!response.ok) throw new Error("팀 목록을 불러오지 못했습니다. 새로고침해 주세요.");
    const teams = await response.json();
    if (!teams.length) throw new Error("등록된 팀이 없습니다. 관리자에게 문의해 주세요.");
    select.replaceChildren(new Option("팀을 선택하세요 (선택 사항)", ""));
    teams.forEach(team => select.add(new Option(team.team_name, team.team_name)));
    select.disabled = false;
  } catch (error) {
    select.replaceChildren(new Option("팀 목록을 불러올 수 없습니다", ""));
    throw error;
  }
}

async function loadCategories() {
  const container = document.getElementById("understanding_areas");
  try {
    const response = await fetch("/api/categories");
    if (!response.ok) throw new Error("분야 목록을 불러오지 못했습니다. 새로고침해 주세요.");
    const categories = await response.json();
    if (!categories.length) throw new Error("등록된 분야가 없습니다. 관리자에게 문의해 주세요.");
    container.replaceChildren();
    categories.forEach(category => {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = category.category_value;
      label.append(input, document.createTextNode(` ${category.category_name}`));
      container.append(label);
    });
  } catch (error) {
    container.textContent = "분야 목록을 불러올 수 없습니다.";
    throw error;
  }
}

async function loadPractices() {
  const select = document.getElementById("practice_status");
  try {
    const response = await fetch("/api/practices");
    if (!response.ok) throw new Error("실습 단계 목록을 불러오지 못했습니다. 새로고침해 주세요.");
    const practices = await response.json();
    if (!practices.length) throw new Error("등록된 실습 단계가 없습니다. 관리자에게 문의해 주세요.");
    select.replaceChildren(new Option("선택하세요", ""));
    practices.forEach(practice => select.add(new Option(practice.practice_status, practice.practice_status)));
    select.disabled = false;
  } catch (error) {
    select.replaceChildren(new Option("실습 단계 목록을 불러올 수 없습니다", ""));
    throw error;
  }
}

async function loadStudyProblems() {
  const container = document.getElementById("hardest_points");
  try {
    const response = await fetch("/api/study-problems");
    if (!response.ok) throw new Error("학습 어려움 목록을 불러오지 못했습니다. 새로고침해 주세요.");
    const problems = await response.json();
    if (!problems.length) throw new Error("등록된 학습 어려움 항목이 없습니다. 관리자에게 문의해 주세요.");
    container.replaceChildren();
    problems.forEach(problem => {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = problem.problem_name;
      label.append(input, document.createTextNode(` ${problem.problem_name}`));
      container.append(label);
    });
  } catch (error) {
    container.textContent = "학습 어려움 목록을 불러올 수 없습니다.";
    throw error;
  }
}

async function loadReviewFrequencies() {
  const select = document.getElementById("review_frequency");
  try {
    const response = await fetch("/api/review-frequencies");
    if (!response.ok) throw new Error("복습 빈도 목록을 불러오지 못했습니다. 새로고침해 주세요.");
    const frequencies = await response.json();
    if (!frequencies.length) throw new Error("등록된 복습 빈도가 없습니다. 관리자에게 문의해 주세요.");
    select.replaceChildren(new Option("선택하세요", ""));
    frequencies.forEach(frequency => select.add(new Option(frequency.frequency_name, frequency.frequency_name)));
    select.disabled = false;
  } catch (error) {
    select.replaceChildren(new Option("복습 빈도 목록을 불러올 수 없습니다", ""));
    throw error;
  }
}

async function loadEvaluationItems(url, containerId) {
  const container = document.getElementById(containerId);
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("환경·시설 목록을 불러오지 못했습니다. 새로고침해 주세요.");
    const items = await response.json();
    if (!items.length) throw new Error("등록된 환경·시설 항목이 없습니다.");
    container.replaceChildren();
    items.forEach(item => {
      const box = document.createElement("fieldset");
      box.className = "evaluation-item";
      box.dataset.itemId = item.id;
      const title = document.createElement("legend");
      title.textContent = item.item_name;
      const ratingLabel = document.createElement("label");
      ratingLabel.textContent = "만족도 (필수)";
      const select = document.createElement("select");
      select.required = true;
      select.add(new Option("선택하세요", ""));
      item.options.forEach(option => select.add(new Option(option, option)));
      ratingLabel.append(select);
      const commentLabel = document.createElement("label");
      commentLabel.textContent = "의견 또는 개선 요청 (선택)";
      const comment = document.createElement("textarea");
      comment.maxLength = 5000;
      comment.placeholder = item.comment_hint;
      commentLabel.append(comment);
      box.append(title, ratingLabel, commentLabel);
      container.append(box);
    });
  } catch (error) {
    container.textContent = "목록을 불러올 수 없습니다.";
    throw error;
  }
}

function evaluationAnswers(containerId) {
  return [...document.querySelectorAll(`#${containerId} fieldset`)].map(box => ({
    item_id: Number(box.dataset.itemId),
    satisfaction: box.querySelector("select").value,
    comment: box.querySelector("textarea").value.trim() || null
  }));
}

async function loadPrefferedOccupations() {
  const container = document.getElementById("career_fields");
  try {
    const response = await fetch("/api/preffered-occupations");
    if (!response.ok) throw new Error("관심 분야 목록을 불러오지 못했습니다. 새로고침해 주세요.");
    const occupations = await response.json();
    if (!occupations.length) throw new Error("등록된 관심 분야가 없습니다. 관리자에게 문의해 주세요.");
    container.replaceChildren();
    occupations.forEach(occupation => {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = occupation.occupation_value;
      label.append(input, document.createTextNode(` ${occupation.occupation_name}`));
      container.append(label);
    });
  } catch (error) {
    container.textContent = "관심 분야 목록을 불러올 수 없습니다.";
    throw error;
  }
}

async function loadSurveyOptions() {
  const button = document.getElementById("submitBtn");
  button.disabled = true;
  try {
    await Promise.all([loadTeams(), loadCategories(), loadPractices(), loadStudyProblems(), loadReviewFrequencies(),
      loadEvaluationItems("/api/learn-env", "learn_env_items"),
      loadEvaluationItems("/api/facillities", "facillities_items"), loadPrefferedOccupations()]);
    button.disabled = false;
  } catch (error) {
    showMessage(error.message, "error");
  }
}

function createRatings() {
  document.querySelectorAll(".rating").forEach(container => {
    const name = container.dataset.name;

    const labels = [
      "1 매우 낮음",
      "2 낮음",
      "3 보통",
      "4 높음",
      "5 매우 높음"
    ];

    container.innerHTML = labels.map((text, index) => {
      const value = index + 1;
      return `
        <label>
          <input
            type="radio"
            name="${name}"
            value="${value}"
            ${value === 3 ? "checked" : ""}
          >
          <span>${text}</span>
        </label>
      `;
    }).join("");
  });
}

function checkedValues(groupId) {
  return [...document.querySelectorAll(`#${groupId} input[type="checkbox"]:checked`)]
    .map(input => input.value);
}

function value(id) {
  return document.getElementById(id).value.trim();
}

function radioValue(name) {
  return Number(document.querySelector(`input[name="${name}"]:checked`)?.value || 0);
}

function showMessage(text, type) {
  const box = document.getElementById("message");
  box.textContent = text;
  box.className = `message ${type}`;
  box.scrollIntoView({ behavior: "smooth", block: "center" });
}

function buildPayload() {
  return {
    student_name: value("student_name"),
    team_name: value("team_name") || null,

    understanding_level: radioValue("understanding_level"),
    understanding_good: value("understanding_good") || null,
    understanding_difficult: value("understanding_difficult") || null,
    understanding_areas: checkedValues("understanding_areas"),

    practice_level: radioValue("practice_level"),
    practice_status: value("practice_status"),
    practice_comment: value("practice_comment") || null,

    hardest_points: checkedValues("hardest_points"),
    hardest_comment: value("hardest_comment") || null,

    review_frequency: value("review_frequency"),
    ai_learning_usage: value("ai_learning_usage") || null,
    improvement_method: value("improvement_method") || null,

    project_role: value("project_role") || null,
    desired_role: value("desired_role") || null,
    collaboration_difficulty: value("collaboration_difficulty") || null,
    project_strength: value("project_strength") || null,
    project_burden: value("project_burden") || null,

    ai_tool_level: radioValue("ai_tool_level"),
    ai_tool_usage: checkedValues("ai_tool_usage"),
    code_understanding: value("code_understanding"),
    ai_tool_comment: value("ai_tool_comment") || null,

    desired_job: value("desired_job") || null,
    career_fields: checkedValues("career_fields"),
    course_career_fit: radioValue("course_career_fit"),
    career_comment: value("career_comment") || null,

    class_speed: value("class_speed"),
    need_more_explanation: value("need_more_explanation") || null,
    practice_amount: value("practice_amount"),
    instructor_support: value("instructor_support") || null,
    learn_env_answers: evaluationAnswers("learn_env_items"),
    facillities_answers: evaluationAnswers("facillities_items")
  };
}

async function submitSurvey(event) {
  event.preventDefault();

  const form = document.getElementById("surveyForm");
  if (!form.reportValidity()) return;

  const button = document.getElementById("submitBtn");
  button.disabled = true;
  button.textContent = "저장 중...";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(buildPayload())
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(
        typeof result.detail === "string"
          ? result.detail
          : "설문 저장 중 오류가 발생했습니다."
      );
    }

    showMessage(
      `설문이 저장되었습니다. 접수번호: ${result.id}`,
      "success"
    );

    form.reset();
    createRatings();
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    button.disabled = false;
    button.textContent = "설문 제출하기";
  }
}

createRatings();
loadSurveyOptions();
document.getElementById("surveyForm").addEventListener("submit", submitSurvey);
