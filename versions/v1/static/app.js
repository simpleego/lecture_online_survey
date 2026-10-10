const API_URL = "/api/surveys";

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
    instructor_support: value("instructor_support") || null
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
document.getElementById("surveyForm").addEventListener("submit", submitSurvey);
